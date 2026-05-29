"""文学知识库数据结构定义"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Source:
    """来源标注"""
    name: str  # 来源名称，如"百度百科"
    url: str  # 来源URL
    crawl_time: str = field(default_factory=lambda: datetime.now().isoformat())  # 爬取时间


@dataclass
class ModuleContent:
    """模块内容"""
    module_id: str  # 模块ID，如"background"
    module_name: str  # 模块名称，如"时代背景"
    content: str  # 内容文本
    sources: list[Source] = field(default_factory=list)  # 来源列表
    images: list[str] = field(default_factory=list)  # 图片URL列表
    word_count: int = 0  # 字数统计

    def __post_init__(self):
        if not self.word_count:
            self.word_count = len(self.content)


@dataclass
class LiteraryWork:
    """文学作品"""
    id: str  # 作品ID，如"li_sao"
    name: str  # 作品名称，如"离骚"
    author: str  # 作者
    dynasty: str  # 朝代
    abstract: str  # 摘要
    modules: dict[str, ModuleContent] = field(default_factory=dict)  # 模块内容字典
    tags: list[str] = field(default_factory=list)  # 标签
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_module(self, module_id: str) -> Optional[ModuleContent]:
        """获取指定模块"""
        return self.modules.get(module_id)

    def add_module(self, module: ModuleContent):
        """添加模块"""
        self.modules[module.module_id] = module
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "author": self.author,
            "dynasty": self.dynasty,
            "abstract": self.abstract,
            "modules": {
                mid: {
                    "module_id": m.module_id,
                    "module_name": m.module_name,
                    "content": m.content,
                    "sources": [{"name": s.name, "url": s.url, "crawl_time": s.crawl_time} for s in m.sources],
                    "images": m.images,
                    "word_count": m.word_count,
                }
                for mid, m in self.modules.items()
            },
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LiteraryWork":
        """从字典创建"""
        modules = {}
        for mid, mdata in data.get("modules", {}).items():
            sources = [Source(**s) for s in mdata.get("sources", [])]
            modules[mid] = ModuleContent(
                module_id=mdata["module_id"],
                module_name=mdata["module_name"],
                content=mdata["content"],
                sources=sources,
                images=mdata.get("images", []),
                word_count=mdata.get("word_count", 0),
            )

        return cls(
            id=data["id"],
            name=data["name"],
            author=data.get("author", ""),
            dynasty=data.get("dynasty", ""),
            abstract=data.get("abstract", ""),
            modules=modules,
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )


# 模块类型定义
MODULE_TYPES = [
    {"id": "background", "name": "时代背景", "keywords": ["背景", "时代", "历史", "创作背景"]},
    {"id": "author", "name": "作者介绍", "keywords": ["作者", "生平", "简介", "生卒"]},
    {"id": "text", "name": "原文注释", "keywords": ["原文", "注释", "翻译", "注解"]},
    {"id": "art", "name": "艺术特色", "keywords": ["艺术", "特色", "手法", "表现手法"]},
    {"id": "famous", "name": "名句赏析", "keywords": ["名句", "名言", "赏析", "名句名篇"]},
    {"id": "influence", "name": "后世影响", "keywords": ["影响", "评价", "地位", "文学地位"]},
]


def get_module_name(module_id: str) -> str:
    """获取模块名称"""
    for m in MODULE_TYPES:
        if m["id"] == module_id:
            return m["name"]
    return module_id
