"""模块定向爬取器 - 按模块类型选择最优源，分两层爬取

策略：
- 第一层：快速概要（摘要级）- 从已有数据或搜索结果中提取
- 第二层：深度详细（完整内容）- 按模块类型选择最优源深入爬取
"""

import logging
from typing import Optional

from .scraper import MultiSourceCrawler, LITERARY_MODULES, LITERARY_DATABASE

logger = logging.getLogger(__name__)

# 各模块的最优爬取源（按优先级排序）
MODULE_OPTIMAL_SOURCES = {
    "background": [
        {"source": "baike", "reason": "百度百科有完整的创作背景章节"},
        {"source": "gushiwen", "reason": "古诗文网有赏析中的背景介绍"},
    ],
    "author": [
        {"source": "gushiwen", "reason": "古诗文网有详细的作者生平"},
        {"source": "baike", "reason": "百度百科有作者词条"},
    ],
    "text": [
        {"source": "gushiwen", "reason": "古诗文网有原文+注释+翻译"},
        {"source": "baike", "reason": "百度百科有部分原文"},
    ],
    "art": [
        {"source": "gushiwen", "reason": "古诗文网有详细赏析"},
        {"source": "baike", "reason": "百度百科有艺术特色章节"},
    ],
    "famous": [
        {"source": "gushiwen", "reason": "古诗文网有名句赏析"},
        {"source": "baike", "reason": "百度百科有名句摘录"},
    ],
    "influence": [
        {"source": "baike", "reason": "百度百科有后世影响章节"},
        {"source": "gushiwen", "reason": "古诗文网有评价内容"},
    ],
}


class ModuleCrawler:
    """模块定向爬取器

    按模块类型选择最优源进行爬取，支持两层策略：
    - 第一层：快速概要 - 从摘要/索引中提取
    - 第二层：深度详细 - 按模块类型定向爬取完整内容
    """

    def __init__(self, crawler: Optional[MultiSourceCrawler] = None):
        self.crawler = crawler or MultiSourceCrawler()

    def crawl_summary(self, query: str) -> dict:
        """第一层：快速概要爬取

        从搜索结果和本地缓存中快速提取各模块概要，
        不进行深度爬取，适合搜索结果概览。

        Returns:
            {
                "query": str,
                "modules": [{
                    "id": str,
                    "name": str,
                    "summary": str,
                    "source": str,
                    "has_detail": bool,  # 是否有深度内容
                }],
            }
        """
        # 先从本地数据库获取
        local_data = LITERARY_DATABASE.get(query, {})

        # 尝试搜索获取摘要
        search_result = None
        for src_name, source in self.crawler.sources.items():
            try:
                result = source.search(query)
                if result:
                    search_result = result
                    break
            except Exception as e:
                logger.warning(f"概要搜索失败 ({src_name}): {e}")

        modules = []
        for module in LITERARY_MODULES:
            summary = ""
            source = ""
            has_detail = False

            # 优先从本地数据库获取
            if local_data.get(module["id"]):
                content = local_data[module["id"]]
                summary = content[:200] + "..." if len(content) > 200 else content
                source = "本地知识库"
                has_detail = True

            # 从搜索结果摘要中提取
            if not summary and search_result:
                abstract = search_result.get("abstract", "")
                if abstract:
                    summary = self._extract_from_abstract(abstract, module)
                    if summary:
                        source = search_result.get("source", "爬取")
                        has_detail = True

            if not summary:
                summary = "暂无概要信息，请点击查看详细内容"
                source = "系统默认"

            modules.append({
                "id": module["id"],
                "name": module["name"],
                "summary": summary,
                "source": source,
                "has_detail": has_detail,
            })

        return {"query": query, "modules": modules}

    def crawl_detail(self, query: str, module_id: str, max_retries: int = 3) -> dict:
        """第二层：深度详细爬取

        按模块类型选择最优源，深入爬取完整内容。

        Args:
            query: 作品名
            module_id: 模块 ID
            max_retries: 最大重试次数

        Returns:
            {
                "module": dict,
                "content": str,
                "sources": [...],
                "images": [...],
            }
        """
        # 找到模块信息
        module_info = next(
            (m for m in LITERARY_MODULES if m["id"] == module_id),
            {"id": module_id, "name": module_id, "keywords": [query]},
        )

        results = {
            "module": module_info,
            "content": "",
            "sources": [],
            "images": [],
        }

        # 1. 检查本地数据库
        local_data = LITERARY_DATABASE.get(query, {})
        if local_data.get(module_id):
            results["content"] = local_data[module_id]
            results["sources"].append({"name": "本地知识库", "url": ""})
            return results

        # 2. 按最优源顺序爬取
        optimal_sources = MODULE_OPTIMAL_SOURCES.get(module_id, ["baike", "gushiwen"])

        for source_config in optimal_sources:
            src_name = source_config["source"]
            source = self.crawler.sources.get(src_name)
            if not source:
                continue

            # 先搜索获取 URL
            search_result = self._retry_search(source, query, max_retries)
            if not search_result:
                continue

            work_url = search_result.get("url", "")
            if not work_url:
                continue

            # 获取模块内容
            module_result = self._retry_get_module(source, work_url, module_id, max_retries)
            if module_result and module_result.get("content"):
                results["content"] = module_result["content"]
                results["sources"].append({
                    "name": module_result.get("source_name", src_name),
                    "url": module_result.get("source_url", work_url),
                })

                # 获取图片
                if module_id in ("text", "art", "famous"):
                    try:
                        images = source.get_images(work_url) if hasattr(source, "get_images") else []
                        results["images"] = images[:5]
                    except Exception:
                        pass

                break  # 成功获取内容，退出循环

        # 3. 如果所有源都失败，尝试其他源
        if not results["content"]:
            for src_name, source in self.crawler.sources.items():
                if src_name in [c["source"] for c in optimal_sources]:
                    continue  # 已经尝试过的源跳过

                search_result = self._retry_search(source, query, max_retries)
                if search_result and search_result.get("url"):
                    module_result = self._retry_get_module(
                        source, search_result["url"], module_id, max_retries
                    )
                    if module_result and module_result.get("content"):
                        results["content"] = module_result["content"]
                        results["sources"].append({
                            "name": module_result.get("source_name", src_name),
                            "url": module_result.get("source_url", search_result["url"]),
                        })
                        break

        # 4. 本地知识库降级
        if not results["content"] and local_data.get(module_id):
            results["content"] = local_data[module_id]
            results["sources"].append({"name": "本地知识库（降级）", "url": ""})

        # 5. 最终兜底
        if not results["content"]:
            results["content"] = f"暂未找到关于「{query}」的{module_info['name']}详细信息。\n\n建议尝试其他关键词或稍后重试。"

        return results

    def _extract_from_abstract(self, abstract: str, module: dict) -> str:
        """从摘要中提取模块相关内容"""
        import re
        keywords = module.get("keywords", [])
        sentences = re.split(r"[。！？；\n]", abstract)

        relevant = []
        for s in sentences:
            s = s.strip()
            if len(s) < 5:
                continue
            for kw in keywords:
                if kw in s:
                    relevant.append(s)
                    break
            if len(relevant) >= 3:
                break

        if relevant:
            result = "。".join(relevant)
            if len(result) > 200:
                result = result[:200] + "..."
            return result
        return ""

    def _retry_search(self, source, query: str, max_retries: int) -> Optional[dict]:
        """带重试的搜索"""
        import time
        for attempt in range(max_retries):
            try:
                result = source.search(query)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"搜索失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 0.5)
        return None

    def _retry_get_module(self, source, url: str, module_id: str, max_retries: int) -> Optional[dict]:
        """带重试的模块内容获取"""
        import time
        for attempt in range(max_retries):
            try:
                result = source.get_module_content(url, module_id)
                if result and result.get("content"):
                    return result
            except Exception as e:
                logger.warning(f"模块获取失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 0.5)
        return None
