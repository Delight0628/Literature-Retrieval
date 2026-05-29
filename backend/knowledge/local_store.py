"""本地 JSON 知识库实现

分层存储结构：
- 索引层：backend/data/index.json
- 详情层：backend/data/works/{work_id}/
"""

import os
import json
import shutil
from datetime import datetime
from typing import Optional
from .schema import LiteraryWork, ModuleContent, Source


# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
INDEX_FILE = os.path.join(DATA_DIR, "index.json")
WORKS_DIR = os.path.join(DATA_DIR, "works")


def ensure_dirs():
    """确保目录存在"""
    os.makedirs(WORKS_DIR, exist_ok=True)


def _work_dir(work_id: str) -> str:
    """获取作品目录"""
    return os.path.join(WORKS_DIR, work_id)


def _meta_file(work_id: str) -> str:
    """获取元数据文件路径"""
    return os.path.join(_work_dir(work_id), "meta.json")


def _module_file(work_id: str, module_id: str) -> str:
    """获取模块文件路径"""
    return os.path.join(_work_dir(work_id), f"{module_id}.json")


# ==================== 索引层操作 ====================

def load_index() -> dict:
    """加载索引"""
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"works": {}, "updated_at": datetime.now().isoformat()}


def save_index(index: dict):
    """保存索引"""
    ensure_dirs()
    index["updated_at"] = datetime.now().isoformat()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def add_to_index(work: LiteraryWork):
    """将作品添加到索引"""
    index = load_index()
    index["works"][work.id] = {
        "id": work.id,
        "name": work.name,
        "author": work.author,
        "dynasty": work.dynasty,
        "abstract": work.abstract[:200] + "..." if len(work.abstract) > 200 else work.abstract,
        "tags": work.tags,
        "module_ids": list(work.modules.keys()),
        "updated_at": work.updated_at,
    }
    save_index(index)


def get_from_index(work_id: str) -> Optional[dict]:
    """从索引获取作品概要"""
    index = load_index()
    return index["works"].get(work_id)


def search_index(keyword: str) -> list[dict]:
    """在索引中搜索（简单关键词匹配）"""
    index = load_index()
    results = []
    keyword_lower = keyword.lower()

    for work_id, work_info in index["works"].items():
        # 检查名称、作者、摘要、标签
        if (
            keyword_lower in work_info["name"].lower()
            or keyword_lower in work_info.get("author", "").lower()
            or keyword_lower in work_info.get("abstract", "").lower()
            or any(keyword_lower in tag.lower() for tag in work_info.get("tags", []))
        ):
            results.append(work_info)

    return results


# ==================== 详情层操作 ====================

def save_work(work: LiteraryWork):
    """保存作品完整数据"""
    ensure_dirs()
    work_dir = _work_dir(work.id)
    os.makedirs(work_dir, exist_ok=True)

    # 保存元数据
    meta = {
        "id": work.id,
        "name": work.name,
        "author": work.author,
        "dynasty": work.dynasty,
        "abstract": work.abstract,
        "tags": work.tags,
        "created_at": work.created_at,
        "updated_at": work.updated_at,
    }
    with open(_meta_file(work.id), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 保存各个模块
    for module_id, module in work.modules.items():
        module_data = {
            "module_id": module.module_id,
            "module_name": module.module_name,
            "content": module.content,
            "sources": [
                {"name": s.name, "url": s.url, "crawl_time": s.crawl_time}
                for s in module.sources
            ],
            "images": module.images,
            "word_count": module.word_count,
        }
        with open(_module_file(work.id, module_id), "w", encoding="utf-8") as f:
            json.dump(module_data, f, ensure_ascii=False, indent=2)

    # 更新索引
    add_to_index(work)


def load_work(work_id: str) -> Optional[LiteraryWork]:
    """加载作品完整数据"""
    meta_path = _meta_file(work_id)
    if not os.path.exists(meta_path):
        return None

    # 加载元数据
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # 加载模块
    work_dir = _work_dir(work_id)
    modules = {}
    if os.path.exists(work_dir):
        for filename in os.listdir(work_dir):
            if filename.endswith(".json") and filename != "meta.json":
                module_id = filename[:-5]  # 移除 .json
                module_path = os.path.join(work_dir, filename)
                with open(module_path, "r", encoding="utf-8") as f:
                    module_data = json.load(f)

                sources = [Source(**s) for s in module_data.get("sources", [])]
                modules[module_id] = ModuleContent(
                    module_id=module_data["module_id"],
                    module_name=module_data["module_name"],
                    content=module_data["content"],
                    sources=sources,
                    images=module_data.get("images", []),
                    word_count=module_data.get("word_count", 0),
                )

    return LiteraryWork(
        id=meta["id"],
        name=meta["name"],
        author=meta.get("author", ""),
        dynasty=meta.get("dynasty", ""),
        abstract=meta.get("abstract", ""),
        modules=modules,
        tags=meta.get("tags", []),
        created_at=meta.get("created_at", ""),
        updated_at=meta.get("updated_at", ""),
    )


def work_exists(work_id: str) -> bool:
    """检查作品是否存在"""
    return os.path.exists(_meta_file(work_id))


def list_works() -> list[str]:
    """列出所有作品ID"""
    index = load_index()
    return list(index["works"].keys())


def delete_work(work_id: str):
    """删除作品"""
    work_dir = _work_dir(work_id)
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

    # 从索引中移除
    index = load_index()
    if work_id in index["works"]:
        del index["works"][work_id]
        save_index(index)


def get_stats() -> dict:
    """获取知识库统计"""
    index = load_index()
    works = index["works"]
    total_modules = sum(len(w.get("module_ids", [])) for w in works.values())

    return {
        "total_works": len(works),
        "total_modules": total_modules,
        "works": list(works.keys()),
    }


# ==================== 备份操作 ====================

def backup_data(backup_name: Optional[str] = None):
    """备份数据"""
    if not backup_name:
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    backup_dir = os.path.join(DATA_DIR, "backups", backup_name)
    if os.path.exists(DATA_DIR):
        shutil.copytree(DATA_DIR, backup_dir, dirs_exist_ok=True)
        return backup_dir
    return None


def init_store():
    """初始化存储目录"""
    ensure_dirs()
    if not os.path.exists(INDEX_FILE):
        save_index({"works": {}, "updated_at": datetime.now().isoformat()})
