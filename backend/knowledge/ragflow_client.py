"""RAGFlow API 客户端 - 封装知识库操作"""

import httpx
from typing import Optional


class RAGFlowClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def create_dataset(self, name: str, chunk_method: str = "naive") -> dict:
        """创建知识库"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/datasets",
                headers=self.headers,
                json={"name": name, "chunk_method": chunk_method},
            )
            resp.raise_for_status()
            return resp.json()

    async def list_datasets(self) -> list:
        """列出所有知识库"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/datasets",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json().get("data", [])

    async def upload_document(self, dataset_id: str, file_path: str, file_name: str) -> dict:
        """上传文档到知识库"""
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                resp = await client.post(
                    f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                    headers={"Authorization": self.headers["Authorization"]},
                    files={"file": (file_name, f, "text/plain")},
                )
            resp.raise_for_status()
            return resp.json()

    async def retrieval(self, dataset_ids: list[str], question: str, top_k: int = 10) -> dict:
        """检索文档"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/retrieval",
                headers=self.headers,
                json={
                    "question": question,
                    "dataset_ids": dataset_ids,
                    "top_k": top_k,
                    "similarity_threshold": 0.1,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_dataset(self, dataset_id: str) -> dict:
        """删除知识库"""
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.base_url}/api/v1/datasets/{dataset_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()
