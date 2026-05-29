"""古诗文网爬虫 - 基于 Scrapling 框架

策略：
1. 使用 Scrapling Fetcher 获取页面
2. 通过搜索页面或直接 URL 获取作品
3. 解析作品页面提取原文、注释、翻译
4. 提取赏析和作者简介
"""

import re
import time
import logging
from typing import Optional
from urllib.parse import quote, urljoin

from scrapling import Fetcher

logger = logging.getLogger(__name__)

# 古诗文网 URL
GUSHIWEN_BASE = "https://www.gushiwen.cn"
GUSHIWEN_SEARCH_URL = "https://www.gushiwen.cn/search.aspx"

# 模块关键词映射到古诗文网内容类型
MODULE_TO_GUSHIWEN_TYPES = {
    "text": ["原文", "译文", "注释"],
    "art": ["赏析", "艺术特色", "创作手法"],
    "background": ["创作背景", "写作背景"],
    "famous": ["名句", "名句赏析"],
    "author": ["作者", "简介", "生平"],
    "influence": ["影响", "评价", "地位"],
}


class GushiwenSource:
    """古诗文网爬虫源（基于 Scrapling）"""

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        self.fetcher = Fetcher()

    def _throttle(self):
        """请求限流"""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_request_time = time.time()

    def _get_page(self, url: str):
        """使用 Scrapling Fetcher 获取页面"""
        self._throttle()
        try:
            page = self.fetcher.get(url)
            return page
        except Exception as e:
            logger.warning(f"古诗文网请求失败 {url}: {e}")
            return None

    def _get_text(self, element) -> str:
        """安全获取元素文本"""
        try:
            return element.text.strip() if element and element.text else ""
        except Exception:
            return ""

    def _get_attr(self, element, attr: str) -> str:
        """安全获取元素属性"""
        try:
            return element.attrib.get(attr, "") if element else ""
        except Exception:
            return ""

    def search(self, query: str) -> Optional[dict]:
        """搜索作品，返回基础信息"""
        # 方式1：通过搜索页面查找诗词链接
        result = self._search_via_search_page(query)
        if result:
            return result

        # 方式2：通过作者标签页查找（不需要登录）
        result = self._search_via_author_page(query)
        if result:
            return result

        # 方式3：尝试直接访问作品页面
        result = self._try_direct_url(query)
        if result:
            return result

        return None

    def _search_via_author_page(self, query: str) -> Optional[dict]:
        """通过作者标签页查找作品（不需要登录，返回该作者的诗词列表）"""
        url = f"{GUSHIWEN_BASE}/shiwens/default.aspx?author={quote(query)}"
        page = self._get_page(url)
        if not page:
            return None

        # 查找诗词链接
        poem_links = page.css("a[href*='shiwenv']")
        if poem_links:
            href = self._get_attr(poem_links[0], "href")
            if href:
                item_url = urljoin(GUSHIWEN_BASE, href)
                return self._parse_work_page(item_url, query)

        return None

    def _search_via_search_page(self, query: str) -> Optional[dict]:
        """通过搜索页面查找作品"""
        url = f"{GUSHIWEN_SEARCH_URL}?value={quote(query)}"
        page = self._get_page(url)
        if not page:
            return None

        # 直接搜索诗词链接（最可靠的选择器）
        poem_links = page.css("a[href*='shiwenv']")
        if poem_links:
            href = self._get_attr(poem_links[0], "href")
            if href:
                item_url = urljoin(GUSHIWEN_BASE, href)
                return self._parse_work_page(item_url, query)

        # 备选：搜索 div.cont 中的链接
        cont_elements = page.css("div.cont")
        if cont_elements:
            for cont in cont_elements:
                links = cont.css("a")
                for link in links:
                    href = self._get_attr(link, "href")
                    if href and "shiwenv" in href:
                        item_url = urljoin(GUSHIWEN_BASE, href)
                        return self._parse_work_page(item_url, query)

        return None

    def _try_direct_url(self, query: str) -> Optional[dict]:
        """尝试直接构造 URL 访问"""
        test_urls = [
            f"{GUSHIWEN_BASE}/shiwenv_{quote(query)}.aspx",
        ]
        for url in test_urls:
            page = self._get_page(url)
            if page:
                # 检查页面是否有内容
                h1 = page.css("h1")
                if h1 and self._get_text(h1[0]):
                    return self._parse_work_page(url, query)
        return None

    def _parse_work_page(self, url: str, query: str) -> Optional[dict]:
        """解析作品页面"""
        page = self._get_page(url)
        if not page:
            return None

        # 提取标题
        title = ""
        h1_elements = page.css("h1")
        if h1_elements:
            title = self._get_text(h1_elements[0])

        # 提取朝代和作者
        dynasty = ""
        author = ""

        source_links = page.css("p.source a")
        if source_links:
            author = self._get_text(source_links[0])

        source_spans = page.css("p.source span")
        if source_spans:
            dynasty = self._get_text(source_spans[0])

        return {
            "title": title or query,
            "url": url,
            "dynasty": dynasty,
            "author": author,
            "source": "古诗文网",
        }

    def get_original_text(self, url: str) -> dict:
        """获取原文、译文、注释"""
        page = self._get_page(url)
        if not page:
            return {"content": "", "translation": "", "annotation": "",
                    "source_url": url, "source_name": "古诗文网"}

        content = ""
        translation = ""
        annotation = ""

        # 提取原文 - 古诗文网页面中，原文在 p 标签中（排除 p.source）
        all_p = page.css("p")
        if all_p:
            text_parts = []
            for p in all_p:
                cls = p.attrib.get("class", "")
                if cls == "source":
                    continue
                t = self._get_text(p)
                if t and len(t) > 5:
                    text_parts.append(t)
            if text_parts:
                content = "\n\n".join(text_parts)

        # 如果 p 标签没有内容，尝试 div.contson
        if not content:
            contson = page.css("div.contson")
            if contson:
                content = self._get_text(contson[0])

        # 如果还没有内容，尝试 div.cont
        if not content:
            cont = page.css("div.cont")
            if cont:
                # 取第一个非空的 cont
                for c in cont:
                    t = self._get_text(c)
                    if t and len(t) > 20:
                        content = t
                        break

        # 提取译文和注释
        translation = self._extract_section(page, ["译文", "翻译", "白话译文"])
        annotation = self._extract_section(page, ["注释", "注解"])

        return {
            "content": content,
            "translation": translation,
            "annotation": annotation,
            "source_url": url,
            "source_name": "古诗文网",
        }

    def get_appreciation(self, url: str) -> str:
        """获取赏析内容"""
        page = self._get_page(url)
        if not page:
            return ""
        return self._extract_section(page, ["赏析", "创作背景", "艺术特色", "鉴赏"])

    def get_author_info(self, author_name: str, author_url: str = "") -> dict:
        """获取作者简介"""
        url = author_url
        if not url:
            url = self._find_author_url(author_name)

        if not url:
            return {
                "name": author_name, "introduction": "", "dynasty": "",
                "source_url": "", "source_name": "古诗文网",
            }

        page = self._get_page(url)
        if not page:
            return {
                "name": author_name, "introduction": "", "dynasty": "",
                "source_url": url, "source_name": "古诗文网",
            }

        introduction = ""
        intro_elements = page.css("div.author-content div.cont")
        if not intro_elements:
            intro_elements = page.css("div.intro")
        if intro_elements:
            introduction = self._get_text(intro_elements[0])

        dynasty = ""
        dynasty_elements = page.css("span.dynasty")
        if not dynasty_elements:
            dynasty_elements = page.css("p.source span")
        if dynasty_elements:
            dynasty = self._get_text(dynasty_elements[0])

        return {
            "name": author_name, "introduction": introduction,
            "dynasty": dynasty, "source_url": url, "source_name": "古诗文网",
        }

    def _find_author_url(self, author_name: str) -> str:
        """查找作者页面 URL"""
        search_url = f"{GUSHIWEN_SEARCH_URL}?value={quote(author_name)}"
        page = self._get_page(search_url)
        if not page:
            return ""

        author_links = page.css("a[href*='authorv_']")
        for link in author_links:
            text = self._get_text(link)
            if author_name in text:
                href = self._get_attr(link, "href")
                return urljoin(GUSHIWEN_BASE, href)
        return ""

    def _extract_section(self, page, section_titles: list[str]) -> str:
        """提取指定章节的内容"""
        # 方法1：通过标题标签匹配
        headings = page.css("h2, h3, h4, span, p")
        for heading in headings:
            heading_text = self._get_text(heading)
            for title in section_titles:
                if title in heading_text:
                    content_parts = []
                    sibling = heading.next
                    while sibling:
                        tag_name = getattr(sibling, "tag", "")
                        if tag_name in ("h2", "h3", "h4"):
                            break
                        text = self._get_text(sibling)
                        if text and len(text) > 3:
                            content_parts.append(text)
                        sibling = sibling.next
                    if content_parts:
                        return "\n\n".join(content_parts)

        # 方法2：通过 div 文本匹配
        divs = page.css("div")
        for div in divs:
            div_text = self._get_text(div)[:20]
            for title in section_titles:
                if title in div_text:
                    full_text = self._get_text(div)
                    if len(full_text) > len(title) + 10:
                        content = full_text.replace(title, "", 1).strip()
                        if content:
                            return content
        return ""

    def get_images(self, url: str) -> list[str]:
        """提取页面中的相关图片 URL"""
        page = self._get_page(url)
        if not page:
            return []

        images = []
        img_elements = page.css("img")
        for img in img_elements:
            src = self._get_attr(img, "src") or self._get_attr(img, "data-src")
            if src and not src.endswith(".gif"):
                full_url = urljoin(GUSHIWEN_BASE, src)
                images.append(full_url)
        return images[:10]

    def get_module_content(self, url: str, module_id: str) -> dict:
        """获取指定模块的详细内容（统一接口）"""
        if module_id == "text":
            text_data = self.get_original_text(url)
            combined = text_data["content"]
            if text_data["translation"]:
                combined += "\n\n【译文】\n" + text_data["translation"]
            if text_data["annotation"]:
                combined += "\n\n【注释】\n" + text_data["annotation"]
            return {"content": combined, "source_url": url, "source_name": "古诗文网"}

        elif module_id == "author":
            page = self._get_page(url)
            if not page:
                return {"content": "", "source_url": url, "source_name": "古诗文网"}

            author_links = page.css("a[href*='authorv']")
            if author_links:
                author_url = urljoin(GUSHIWEN_BASE, self._get_attr(author_links[0], "href"))
                author_name = self._get_text(author_links[0])
                info = self.get_author_info(author_name, author_url)
                return {
                    "content": info["introduction"] or f"暂无{author_name}的详细介绍",
                    "source_url": author_url, "source_name": "古诗文网",
                }

        elif module_id in ("art", "famous", "background", "influence"):
            section_titles = MODULE_TO_GUSHIWEN_TYPES.get(module_id, [])
            content = self.get_appreciation(url)
            if not content:
                page = self._get_page(url)
                if page:
                    content = self._extract_section(page, section_titles)
            return {"content": content, "source_url": url, "source_name": "古诗文网"}

        return {"content": "", "source_url": url, "source_name": "古诗文网"}
