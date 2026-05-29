"""爬虫模块 - 多源爬虫管理器

提供统一的爬取接口，支持百度百科、古诗文网等多个数据源。
"""

from .scraper import MultiSourceCrawler, general_search, deep_search, LITERARY_MODULES

__all__ = [
    "MultiSourceCrawler",
    "general_search",
    "deep_search",
    "LITERARY_MODULES",
]
