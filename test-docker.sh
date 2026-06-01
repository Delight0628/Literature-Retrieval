#!/bin/bash

# 本地 Docker 测试脚本
# 在部署到 Railway 之前，先本地测试 Docker 构建

set -e

echo "🐳 开始本地 Docker 测试..."
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 未安装 Docker"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 构建前端
echo "🔨 构建前端..."
cd frontend
npm install
npm run build
cd ..

# 构建 Docker 镜像
echo "📦 构建 Docker 镜像..."
docker build -t literary-search-test .

# 运行容器
echo "🚀 启动容器..."
echo "   访问地址: http://localhost:7000"
echo "   按 Ctrl+C 停止"
echo ""

docker run -p 7000:7000 \
    -e DIFY_API_KEY=${DIFY_API_KEY:-""} \
    -e DIFY_API_URL=${DIFY_API_URL:-""} \
    -e DIFY_DATASET_ID=${DIFY_DATASET_ID:-""} \
    literary-search-test