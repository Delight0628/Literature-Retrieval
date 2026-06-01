"""FastAPI 主入口"""

import sys
import os

# 确保 backend 目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    allow_origins=["*"],  # 生产环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/test")
async def test_endpoint(data: dict):
    """测试端点：用于调试请求体解析问题"""
    print(f"[DEBUG] 收到测试请求: {data}")
    # 尝试重新编码以修复中文字符问题
    import json
    try:
        # 如果 data 中有乱码，尝试重新解码
        fixed_data = {}
        for k, v in data.items():
            if isinstance(v, str):
                # 尝试用 latin-1 解码后再用 utf-8 解码
                try:
                    fixed_v = v.encode('latin-1').decode('utf-8')
                    fixed_data[k] = fixed_v
                except:
                    fixed_data[k] = v
            else:
                fixed_data[k] = v
        return {"received": fixed_data, "status": "ok"}
    except Exception as e:
        print(f"[DEBUG] 修复字符编码失败: {e}")
        return {"received": data, "status": "ok"}


# 注册 API 路由
app.include_router(search_router)
app.include_router(knowledge_router)

# 静态文件目录（前端构建产物）
# 优先使用环境变量，否则使用相对路径（本地开发）
STATIC_DIR = os.environ.get('STATIC_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist'))

# Railway 部署时的备用路径
if not os.path.exists(STATIC_DIR):
    STATIC_DIR = '/app/dist'

# 打印静态文件目录路径（调试用）
print(f"[INFO] 静态文件目录: {STATIC_DIR}")
print(f"[INFO] 静态文件目录存在: {os.path.exists(STATIC_DIR)}")

# 如果静态文件目录存在，挂载静态文件服务
if os.path.exists(STATIC_DIR):
    # 挂载 assets 目录（JS、CSS 等静态资源）
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        print(f"[INFO] 已挂载 assets 目录: {assets_dir}")

    @app.get("/")
    async def serve_index():
        """首页路由：返回 index.html"""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA 路由回退：所有非 API 路由都返回 index.html"""
        # 如果是具体的文件，直接返回
        file_path = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        # 否则返回 index.html（SPA 路由）
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    print(f"[WARNING] 静态文件目录不存在: {STATIC_DIR}")

    @app.get("/")
    async def root():
        return {"message": "文学知识检索系统 API"}


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
