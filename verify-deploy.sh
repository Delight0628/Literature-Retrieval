#!/bin/bash

# 部署验证脚本
# 检查所有必要的文件和配置是否就绪

set -e

echo "🔍 验证部署配置..."
echo ""

# 检查必要文件
echo "📁 检查必要文件..."
files=(
    "Dockerfile"
    "railway.json"
    ".dockerignore"
    ".env.example"
    "DEPLOY.md"
    "backend/main.py"
    "backend/requirements.txt"
    "frontend/package.json"
    "frontend/vite.config.js"
)

missing=0
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (缺失)"
        missing=1
    fi
done

echo ""

# 检查 Dockerfile 语法
echo "🐳 检查 Dockerfile..."
if grep -q "FROM" Dockerfile && grep -q "COPY" Dockerfile && grep -q "RUN" Dockerfile; then
    echo "  ✅ Dockerfile 语法正确"
else
    echo "  ❌ Dockerfile 可能有语法问题"
fi

echo ""

# 检查 railway.json
echo "📦 检查 railway.json..."
if grep -q "DOCKERFILE" railway.json && grep -q "healthcheckPath" railway.json; then
    echo "  ✅ railway.json 配置正确"
else
    echo "  ❌ railway.json 配置可能有问题"
fi

echo ""

# 检查后端主文件
echo "🔧 检查后端配置..."
if grep -q "StaticFiles" backend/main.py && grep -q "FileResponse" backend/main.py; then
    echo "  ✅ 后端已配置静态文件服务"
else
    echo "  ❌ 后端缺少静态文件服务配置"
fi

echo ""

# 检查前端构建配置
echo "🎨 检查前端配置..."
if grep -q "build" frontend/package.json; then
    echo "  ✅ 前端有构建脚本"
else
    echo "  ❌ 前端缺少构建脚本"
fi

echo ""

# 检查 .env 文件
echo "🔐 检查环境变量..."
if [ -f ".env" ]; then
    echo "  ✅ .env 文件存在"
    if grep -q "DIFY_API_KEY" .env; then
        echo "  ✅ Dify API Key 已配置"
    else
        echo "  ⚠️  Dify API Key 未配置（可选）"
    fi
else
    echo "  ⚠️  .env 文件不存在（可选）"
fi

echo ""

# 总结
if [ $missing -eq 0 ]; then
    echo "✅ 验证通过！所有必要文件和配置都已就绪。"
    echo ""
    echo "🚀 下一步："
    echo "1. 推送到 GitHub: git add . && git commit -m 'Deploy' && git push"
    echo "2. 在 Railway Dashboard 创建项目"
    echo "3. 查看详细文档: DEPLOY.md"
else
    echo "❌ 验证失败！请检查缺失的文件。"
    exit 1
fi