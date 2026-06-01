#!/bin/bash

# Railway 快速部署脚本
# 使用方法: ./deploy.sh

set -e

echo "🚀 开始部署文学知识检索系统到 Railway..."

# 检查是否安装了 Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ 未安装 Railway CLI"
    echo "请先安装: npm install -g @railway/cli"
    exit 1
fi

# 检查是否登录
if ! railway whoami &> /dev/null; then
    echo "🔐 请先登录 Railway"
    railway login
fi

# 检查是否已初始化
if [ ! -f ".railway/config.json" ]; then
    echo "📦 初始化 Railway 项目..."
    railway init
fi

# 构建前端
echo "🔨 构建前端..."
cd frontend
npm install
npm run build
cd ..

# 部署到 Railway
echo "🚀 部署到 Railway..."
railway up

echo "✅ 部署完成！"
echo ""
echo "📋 后续步骤:"
echo "1. 访问 Railway Dashboard: https://railway.app/dashboard"
echo "2. 配置环境变量（Dify API Key 等）"
echo "3. 设置域名（可选）"
echo "4. 配置 Volume 进行数据持久化（可选）"
echo ""
echo "📚 详细文档请查看 DEPLOY.md"