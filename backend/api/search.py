"""搜索相关 API 路由"""

import sys
import os

# 确保 backend 目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from crawler.scraper import general_search, deep_search
from knowledge.ragflow_client import RAGFlowClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '.env'))

router = APIRouter(prefix="/api", tags=["search"])

# 初始化 RAGFlow 客户端
ragflow = RAGFlowClient(
    base_url=os.getenv("RAGFLOW_API_URL", "http://localhost:9380"),
    api_key=os.getenv("RAGFLOW_API_KEY", ""),
)


class SearchRequest(BaseModel):
    query: str


class DeepSearchRequest(BaseModel):
    query: str
    module_id: str


class DownloadRequest(BaseModel):
    query: str
    module_id: str
    content: str


@router.post("/search")
async def search(request: SearchRequest):
    """泛化检索 - 返回模块列表和概要"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")

    result = general_search(request.query)
    return result


@router.post("/search/deep")
async def search_deep(request: DeepSearchRequest):
    """深度检索 - 获取指定模块的详细内容"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")

    result = deep_search(request.query, request.module_id)
    return result


@router.post("/download")
async def download(request: DownloadRequest):
    """生成文档下载"""
    from fastapi.responses import StreamingResponse
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    import io

    doc = Document()

    title = doc.add_heading(f"{request.query} - {request.module_id}", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(request.content)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename={request.query}_{request.module_id}.docx"
        },
    )


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
