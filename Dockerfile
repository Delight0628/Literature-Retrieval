# 多阶段构建：前端构建 + 后端运行

# 阶段 1：构建前端
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制前端源码
COPY frontend/ ./

# 构建前端
RUN npm run build

# 阶段 2：运行后端
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（scrapling 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制后端依赖文件
COPY backend/requirements.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源码
COPY backend/ ./

# 复制前端构建产物到根目录的 dist 文件夹
COPY --from=frontend-builder /app/frontend/dist ./dist

# 创建数据目录
RUN mkdir -p /app/backend/data

# 暴露端口
EXPOSE 7000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7000"]