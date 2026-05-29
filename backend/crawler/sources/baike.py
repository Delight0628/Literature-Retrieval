"""百度百科爬虫 - 基于 Scrapling 框架

策略：
1. 使用 Scrapling Fetcher 获取页面
2. 检测 CAPTCHA 页面，自动降级
3. 解析词条页面提取概述、目录结构、infobox
4. 按目录模块分别爬取详细内容
"""

import re
import time
import logging
from typing import Optional
from urllib.parse import quote

from scrapling import Fetcher

logger = logging.getLogger(__name__)

# 百度百科 URL
BAIKE_SEARCH_URL = "https://baike.baidu.com/search"
BAIKE_ITEM_URL = "https://baike.baidu.com/item/"

# 模块关键词映射到百度百科目录标题
MODULE_TO_BAIKE_SECTIONS = {
    "background": ["创作背景", "写作背景", "背景", "历史背景", "时代背景"],
    "author": ["作者简介", "作者介绍", "人物生平", "生平", "作者"],
    "text": ["原文", "作品原文", "全文", "节选", "内容"],
    "art": ["艺术特色", "艺术手法", "创作手法", "艺术成就", "赏析"],
    "famous": ["名句", "经典名句", "名句赏析", "名言", "名篇"],
    "influence": ["后世影响", "影响", "文学地位", "评价", "社会影响"],
}


class BaikeSource:
    """百度百科爬虫源（基于 Scrapling）"""

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
            # 检测 CAPTCHA 页面
            final_url = str(page.url) if hasattr(page, "url") else url
            if "captcha" in final_url.lower() or "anticrawl" in final_url.lower():
                logger.warning(f"百度百科 CAPTCHA 拦截: {final_url}")
                return None
            return page
        except Exception as e:
            logger.warning(f"百度百科请求失败 {url}: {e}")
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
        url = BAIKE_ITEM_URL + quote(query)
        page = self._get_page(url)
        if not page:
            return None

        content_divs = page.css("div.content")
        if not content_divs:
            return self._search_via_search_page(query)

        abstract = self._extract_abstract(page)
        infobox = self._extract_infobox(page)

        return {
            "title": query,
            "url": url,
            "abstract": abstract,
            "source": "百度百科",
            "infobox": infobox,
        }

    def _search_via_search_page(self, query: str) -> Optional[dict]:
        """通过搜索页面查找词条"""
        url = f"{BAIKE_SEARCH_URL}?word={quote(query)}"
        page = self._get_page(url)
        if not page:
            return None

        results = page.css("div.search-result a[href*='/item/']")
        if not results:
            return None

        item_url = self._get_attr(results[0], "href")
        if not item_url:
            return None
        if item_url.startswith("/"):
            item_url = "https://baike.baidu.com" + item_url

        item_page = self._get_page(item_url)
        if not item_page:
            return None

        abstract = self._extract_abstract(item_page)
        infobox = self._extract_infobox(item_page)

        title_elements = item_page.css("span.lemma-title")
        title = self._get_text(title_elements[0]) if title_elements else query

        return {
            "title": title,
            "url": item_url,
            "abstract": abstract,
            "source": "百度百科",
            "infobox": infobox,
        }

    def _extract_abstract(self, page) -> str:
        """提取词条摘要"""
        selectors = [
            "div.lemma-summary",
            "div.summary",
            "div.abstract",
            "div.content div.paragraph",
        ]
        for selector in selectors:
            elements = page.css(selector)
            if elements:
                text = self._get_text(elements[0])
                if len(text) > 30:
                    return text

        content_divs = page.css("div.content")
        if content_divs:
            paragraphs = content_divs[0].css("p")
            for p in paragraphs:
                text = self._get_text(p)
                if len(text) > 30:
                    return text
        return ""

    def _extract_infobox(self, page) -> dict:
        """提取 infobox 结构化数据"""
        infobox = {}
        tables = page.css("table")
        for table in tables:
            table_text = self._get_text(table)[:50]
            if "basic" in table_text.lower() or "info" in table_text.lower():
                rows = table.css("tr")
                for row in rows:
                    th_elements = row.css("th")
                    td_elements = row.css("td")
                    if th_elements and td_elements:
                        key = self._get_text(th_elements[0])
                        value = self._get_text(td_elements[0])
                        if key and value:
                            infobox[key] = value
                if infobox:
                    break
        return infobox

    def get_module_content(self, url: str, module_id: str) -> dict:
        """获取指定模块的详细内容"""
        page = self._get_page(url)
        if not page:
            return {"content": "", "source_url": url, "source_name": "百度百科"}

        section_titles = MODULE_TO_BAIKE_SECTIONS.get(module_id, [])
        content = self._extract_section_by_heading(page, section_titles)

        if not content:
            content = self._extract_section_by_text(page, section_titles)

        if not content:
            abstract = self._extract_abstract(page)
            if abstract:
                content = self._extract_relevant_sentences(abstract, section_titles)

        return {
            "content": content,
            "source_url": url,
            "source_name": "百度百科",
        }

    def _extract_section_by_heading(self, page, section_titles: list[str]) -> str:
        """通过标题标签匹配提取章节内容"""
        headings = page.css("h2, h3")
        for heading in headings:
            heading_text = self._get_text(heading)
            heading_text = re.sub(r"\[编辑\]", "", heading_text).strip()

            for title in section_titles:
                if title in heading_text:
                    content_parts = []
                    sibling = heading.next
                    while sibling:
                        tag_name = getattr(sibling, "tag", "")
                        if tag_name in ("h2", "h3"):
                            break
                        text = self._get_text(sibling)
                        if text:
                            content_parts.append(text)
                        sibling = sibling.next
                    if content_parts:
                        return "\n\n".join(content_parts)
        return ""

    def _extract_section_by_text(self, page, section_titles: list[str]) -> str:
        """通过全文文本正则匹配提取章节"""
        try:
            html = page.html_content if hasattr(page, "html_content") else str(page)
        except Exception:
            html = ""

        for title in section_titles:
            pattern = re.compile(
                rf"{re.escape(title)}[^\n]*\n(.*?)(?=\n[一二三四五六七八九十]+[、.]\s*\S|\Z)",
                re.DOTALL,
            )
            match = pattern.search(html)
            if match:
                content = match.group(1).strip()
                if len(content) > 20:
                    return content
        return ""

    def _extract_relevant_sentences(self, text: str, keywords: list[str]) -> str:
        """从文本中提取包含关键词的相关句子"""
        sentences = re.split(r"[。！？；\n]", text)
        relevant = []
        for s in sentences:
            s = s.strip()
            if len(s) < 5:
                continue
            for kw in keywords:
                if kw in s:
                    relevant.append(s)
                    break
            if len(relevant) >= 5:
                break
        return "。".join(relevant) + "。" if relevant else ""

    def get_images(self, url: str) -> list[str]:
        """提取页面中的相关图片 URL"""
        page = self._get_page(url)
        if not page:
            return []

        images = []
        imgs = page.css("img")
        for img in imgs:
            src = self._get_attr(img, "src") or self._get_attr(img, "data-src")
            if src and "baikepic" in src:
                if not src.startswith("http"):
                    src = "https:" + src if src.startswith("//") else src
                images.append(src)
        return images[:10]
