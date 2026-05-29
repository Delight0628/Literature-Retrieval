"""知识库管理 API 路由

管理本地 JSON 知识库
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from knowledge.local_store import (
    list_works, load_work, get_stats, delete_work, init_store
)
from knowledge.migrate import migrate_data

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# 初始化知识库
init_store()


@router.get("/stats")
async def get_knowledge_stats():
    """获取知识库统计"""
    stats = get_stats()
    return stats


@router.get("/works")
async def list_all_works():
    """列出所有作品"""
    work_ids = list_works()
    works = []
    for work_id in work_ids:
        work = load_work(work_id)
        if work:
            works.append({
                "id": work.id,
                "name": work.name,
                "author": work.author,
                "dynasty": work.dynasty,
                "module_count": len(work.modules),
                "tags": work.tags,
            })
    return {"works": works}


@router.get("/works/{work_id}")
async def get_work_detail(work_id: str):
    """获取作品详情"""
    work = load_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail=f"未找到作品: {work_id}")

    return work.to_dict()


@router.delete("/works/{work_id}")
async def delete_work_api(work_id: str):
    """删除作品"""
    from knowledge.local_store import work_exists
    if not work_exists(work_id):
        raise HTTPException(status_code=404, detail=f"未找到作品: {work_id}")

    delete_work(work_id)
    return {"message": f"已删除作品: {work_id}"}


@router.post("/migrate")
async def trigger_migrate():
    """触发数据迁移（从硬编码数据导入）"""
    try:
        migrate_data()
        return {"message": "数据迁移完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"迁移失败: {str(e)}")
