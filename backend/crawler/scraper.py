"""多源爬虫管理器 - 统一调度多个爬取源

架构：
- MultiSourceCrawler：统一调度器，管理多个爬取源
- 请求限流 + 错误重试 + 降级策略
- 缓存检查优先，无缓存时触发多源爬取
"""

import sys
import re
import json
import time
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

from .sources.baike import BaikeSource
from .sources.gushiwen import GushiwenSource

# 文学作品主题模块定义
LITERARY_MODULES = [
    {"id": "background", "name": "时代背景", "keywords": ["背景", "时代", "历史", "创作背景"]},
    {"id": "author", "name": "作者介绍", "keywords": ["作者", "生平", "简介", "屈原"]},
    {"id": "text", "name": "原文注释", "keywords": ["原文", "注释", "翻译", "注解"]},
    {"id": "art", "name": "艺术特色", "keywords": ["艺术", "特色", "手法", "表现手法"]},
    {"id": "famous", "name": "名句赏析", "keywords": ["名句", "名言", "赏析", "名句名篇"]},
    {"id": "influence", "name": "后世影响", "keywords": ["影响", "评价", "地位", "文学地位"]},
]


class MultiSourceCrawler:
    """多源爬虫管理器

    功能：
    - 统一调度多个爬取源（百度百科、古诗文网等）
    - 请求限流：每源每秒最多 1 次请求
    - 错误重试：失败自动重试 3 次（指数退避）
    - 降级策略：某源失败用其他源降级
    - 自动保存到本地知识库
    """

    def __init__(self):
        self.sources = {
            "baike": BaikeSource(rate_limit=1.0),
            "gushiwen": GushiwenSource(rate_limit=1.0),
        }

        # 各模块的优先源顺序
        self.module_source_priority = {
            "background": ["baike", "gushiwen"],
            "author": ["gushiwen", "baike"],
            "text": ["gushiwen", "baike"],
            "art": ["gushiwen", "baike"],
            "famous": ["gushiwen", "baike"],
            "influence": ["baike", "gushiwen"],
        }

    def search(self, query: str, max_retries: int = 3) -> dict:
        """泛化搜索 - 尝试多个源获取作品信息

        Args:
            query: 搜索关键词
            max_retries: 每个源的最大重试次数

        Returns:
            {
                "query": str,
                "modules": [...],
                "title": str,
                "work_url": str,
            }
        """
        # 1. 按优先级尝试各源搜索
        search_result = None
        source_name = ""
        for src_name, source in self.sources.items():
            result = self._retry_search(source, query, max_retries)
            if result:
                search_result = result
                source_name = src_name
                break

        if not search_result:
            # 所有源都失败，返回空模块列表
            return self._build_empty_result(query)

        # 2. 构建模块列表
        work_url = search_result.get("url", "")
        modules = self._build_module_summaries(query, work_url, source_name, max_retries)

        return {
            "query": query,
            "title": search_result.get("title", query),
            "work_url": work_url,
            "modules": modules,
        }

    def deep_search(self, query: str, module_id: str, max_retries: int = 3) -> dict:
        """深度搜索 - 获取指定模块的详细内容

        Args:
            query: 搜索关键词
            module_id: 模块 ID
            max_retries: 每个源的最大重试次数

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

        # 1. 先尝试从本地知识库获取
        try:
            from ..knowledge.local_store import work_exists, load_work
            from ..knowledge.search_engine import search_works

            # 搜索作品
            works = search_works(query)
            if works:
                work_id = works[0]["id"]
                if work_exists(work_id):
                    work = load_work(work_id)
                    if work and module_id in work.modules:
                        module = work.modules[module_id]
                        results["content"] = module.content
                        results["sources"] = [
                            {"name": s.name, "url": s.url}
                            for s in module.sources
                        ]
                        results["images"] = module.images
                        return results
        except Exception as e:
            logger.warning(f"本地知识库查询失败: {e}")

        # 2. 按模块优先级尝试各源爬取
        priority = self.module_source_priority.get(module_id, ["baike", "gushiwen"])

        # 先搜索获取 URL
        search_result = None
        source_name = ""
        for src_name in priority:
            source = self.sources.get(src_name)
            if not source:
                continue
            result = self._retry_search(source, query, max_retries)
            if result:
                search_result = result
                source_name = src_name
                break

        # 如果优先源都失败，尝试其他源
        if not search_result:
            for src_name, source in self.sources.items():
                if src_name not in priority:
                    result = self._retry_search(source, query, max_retries)
                    if result:
                        search_result = result
                        source_name = src_name
                        break

        if not search_result:
            results["content"] = f"暂未找到关于「{query}」的{module_info['name']}详细信息。"
            return results

        work_url = search_result.get("url", "")

        # 3. 获取模块详细内容
        source = self.sources[source_name]
        module_result = self._retry_get_module(source, work_url, module_id, max_retries)

        if module_result and module_result.get("content"):
            results["content"] = module_result["content"]
            results["sources"].append({
                "name": module_result.get("source_name", source_name),
                "url": module_result.get("source_url", work_url),
            })

        # 4. 获取图片（仅首次请求时）
        if module_id in ("text", "art", "famous"):
            try:
                images = source.get_images(work_url) if hasattr(source, 'get_images') else []
                results["images"] = images[:5]
            except Exception:
                pass

        # 5. 如果内容仍然为空，返回默认提示
        if not results["content"]:
            results["content"] = f"暂未找到关于「{query}」的{module_info['name']}详细信息。\n\n建议尝试其他关键词或稍后重试。"

        # 6. 保存爬取结果到本地知识库
        if results["content"] and results["sources"]:
            modules_data = {module_id: results["content"]}
            self._save_to_local_store(query, work_url, source_name, modules_data)

        return results

    def _retry_search(self, source, query: str, max_retries: int) -> Optional[dict]:
        """带重试的搜索"""
        for attempt in range(max_retries):
            try:
                result = source.search(query)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"搜索失败 (源: {source.__class__.__name__}, 尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # 指数退避
                    wait = (2 ** attempt) * 0.5
                    time.sleep(wait)
        return None

    def _retry_get_module(self, source, url: str, module_id: str, max_retries: int) -> Optional[dict]:
        """带重试的模块内容获取"""
        for attempt in range(max_retries):
            try:
                result = source.get_module_content(url, module_id)
                if result and result.get("content"):
                    return result
            except Exception as e:
                logger.warning(f"模块内容获取失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait = (2 ** attempt) * 0.5
                    time.sleep(wait)
        return None

    def _build_module_summaries(self, query: str, work_url: str, source_name: str, max_retries: int) -> list[dict]:
        """构建模块概要列表"""
        modules = []
        source = self.sources.get(source_name)

        # 尝试从本地知识库获取
        local_modules = {}
        try:
            from ..knowledge.search_engine import search_works, get_work_modules
            works = search_works(query)
            if works:
                work_id = works[0]["id"]
                modules_result = get_work_modules(work_id)
                for m in modules_result.get("modules", []):
                    local_modules[m["id"]] = m
        except Exception as e:
            logger.warning(f"本地知识库查询失败: {e}")

        for module in LITERARY_MODULES:
            summary = ""
            module_source = ""
            module_url = ""

            # 1. 优先从本地知识库获取
            if module["id"] in local_modules:
                local_m = local_modules[module["id"]]
                if local_m.get("summary") and local_m["summary"] != "暂无概要信息":
                    summary = local_m["summary"]
                    module_source = local_m.get("source", "本地知识库")
                    module_url = local_m.get("source_url", "")

            # 2. 尝试从爬虫源获取
            if not summary and source and work_url:
                try:
                    result = source.get_module_content(work_url, module["id"])
                    if result and result.get("content"):
                        content = result["content"]
                        summary = content[:200] + "..." if len(content) > 200 else content
                        module_source = result.get("source_name", source_name)
                        module_url = result.get("source_url", work_url)
                except Exception:
                    pass

            # 3. 摘要提取降级
            if not summary and source and work_url:
                try:
                    search_result = source.search(query)
                    if search_result and search_result.get("abstract"):
                        summary = self._extract_module_from_abstract(
                            search_result["abstract"], module
                        )
                        if summary:
                            module_source = search_result.get("source", source_name)
                            module_url = search_result.get("url", work_url)
                except Exception:
                    pass

            if not summary:
                summary = "暂无概要信息，请点击查看详细内容"
                module_source = "系统默认"

            modules.append({
                "id": module["id"],
                "name": module["name"],
                "summary": summary,
                "source": module_source,
                "source_url": module_url or work_url,
            })

        return modules

    def _extract_module_from_abstract(self, abstract: str, module: dict) -> str:
        """从摘要文本中提取与特定模块相关的内容"""
        keywords = module.get("keywords", [])
        sentences = re.split(r'[。！？；\n]', abstract)

        relevant_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 5:
                continue
            for keyword in keywords:
                if keyword in sentence:
                    relevant_sentences.append(sentence)
                    break

        if relevant_sentences:
            result = "。".join(relevant_sentences[:3])
            if len(result) > 200:
                result = result[:200] + "..."
            return result
        return ""

    def _get_local_fallback(self, query: str, module_id: str) -> str:
        """从本地知识库获取降级内容"""
        try:
            from ..knowledge.search_engine import search_works, get_module_detail
            works = search_works(query)
            if works:
                work_id = works[0]["id"]
                detail = get_module_detail(work_id, module_id)
                if "content" in detail:
                    return detail["content"]
        except Exception as e:
            logger.warning(f"本地知识库降级查询失败: {e}")
        return ""

    def _save_to_local_store(self, query: str, work_url: str, source_name: str, modules_data: dict):
        """将爬取结果保存到本地知识库"""
        try:
            from ..knowledge.schema import LiteraryWork, ModuleContent, Source
            from ..knowledge.local_store import save_work

            # 生成 work_id
            work_id = query.lower().replace(" ", "_").replace("（", "").replace("）", "")

            # 构建模块
            modules = {}
            for module_id, content in modules_data.items():
                if content:
                    module_info = next(
                        (m for m in LITERARY_MODULES if m["id"] == module_id),
                        {"id": module_id, "name": module_id, "keywords": []}
                    )
                    modules[module_id] = ModuleContent(
                        module_id=module_id,
                        module_name=module_info["name"],
                        content=content,
                        sources=[Source(name=source_name, url=work_url)],
                    )

            # 创建作品
            work = LiteraryWork(
                id=work_id,
                name=query,
                author="",
                dynasty="",
                abstract=modules_data.get("abstract", ""),
                modules=modules,
                tags=[],
            )

            # 保存
            save_work(work)
            logger.info(f"已保存爬取结果到本地知识库: {query}")
        except Exception as e:
            logger.warning(f"保存到本地知识库失败: {e}")

    def _build_empty_result(self, query: str) -> dict:
        """构建空结果"""
        modules = []
        for module in LITERARY_MODULES:
            modules.append({
                "id": module["id"],
                "name": module["name"],
                "summary": "暂无概要信息，请点击查看详细内容",
                "source": "系统默认",
                "source_url": "",
            })
        return {"query": query, "modules": modules, "title": query, "work_url": ""}


# ==================== 公共接口函数（保持向后兼容） ====================


def _normalize_query(query: str) -> str:
    """标准化查询关键词，支持中英文模糊匹配"""
    en_to_cn = {
        "li sao": "离骚",
        "li Sao": "离骚",
        "lisao": "离骚",
        "hong lou meng": "红楼梦",
        "dream of the red chamber": "红楼梦",
        "teng wang ge xu": "滕王阁序",
        "preface to the prince teng's pavilion": "滕王阁序",
    }
    query_lower = query.lower().strip()
    if query_lower in en_to_cn:
        return en_to_cn[query_lower]

    # 从本地知识库查找
    try:
        from ..knowledge.local_store import search_index
        results = search_index(query)
        if results:
            return results[0]["name"]
    except Exception:
        pass

    return query


# 全局爬虫实例
_crawler = None


def _get_crawler() -> MultiSourceCrawler:
    """获取全局爬虫实例"""
    global _crawler
    if _crawler is None:
        _crawler = MultiSourceCrawler()
    return _crawler


def general_search(query: str) -> dict:
    """第一层：泛化检索 - 获取模块列表和概要（向后兼容接口）"""
    normalized_query = _normalize_query(query)
    crawler = _get_crawler()
    result = crawler.search(normalized_query)
    # 保持原有返回格式
    return {"query": query, "modules": result.get("modules", [])}


def deep_search(query: str, module_id: str) -> dict:
    """第二层：深度检索 - 获取选定模块的详细内容（向后兼容接口）"""
    normalized_query = _normalize_query(query)
    crawler = _get_crawler()
    return crawler.deep_search(normalized_query, module_id)
