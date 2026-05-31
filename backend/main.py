"""FastAPI 主入口"""

import sys
import os

# 确保 backend 目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.search import router as search_router
from api.knowledge import router as knowledge_router
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

app = FastAPI(
    title="文学知识检索系统",
    description="支持双层权威信息抓取的文学知识检索与展示系统",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(search_router)
app.include_router(knowledge_router)


@app.get("/")
async def root():
    return {"message": "文学知识检索系统 API"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    import socket

    def find_available_port(start_port, host="0.0.0.0"):
        """从 start_port 开始依次尝试，找到第一个可用端口"""
        port = start_port
        while port < start_port + 100:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((host, port))
                    return port
                except OSError:
                    port += 1
        raise RuntimeError(f"在 {start_port}-{start_port + 99} 范围内未找到可用端口")

    target_port = find_available_port(8002)
    if target_port != 8002:
        print(f"[WARNING] 默认端口 8002 被占用，切换到端口 {target_port}")
    print(f"[INFO] 后端服务启动于 http://0.0.0.0:{target_port}")
    uvicorn.run(app, host="0.0.0.0", port=target_port)
