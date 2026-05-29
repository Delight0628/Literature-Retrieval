"""爬取源模块 - 提供多源爬虫的统一接口"""

from .baike import BaikeSource
from .gushiwen import GushiwenSource

__all__ = ["BaikeSource", "GushiwenSource"]
