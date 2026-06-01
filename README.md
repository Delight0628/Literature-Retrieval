# 文学知识检索与展示系统

支持双层权威信息抓取（泛化索引 + 深度挖掘）、分层本地知识库、React 前端交互展示。

## 技术栈

- **爬虫**: Scrapling
- **知识库**: 本地 JSON + Dify API（可选）
- **后端**: Python FastAPI
- **前端**: React + Vite
- **部署**: Railway（轻量级公网部署）

## 快速启动

### 1. 配置环境变量

编辑 `.env` 文件，填入 Dify 的 API 地址和密钥（可选）：

```
DIFY_API_URL=https://api.dify.ai/v1
DIFY_API_KEY=your-api-key
DIFY_DATASET_ID=your-dataset-id
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问系统

打开浏览器访问 http://localhost:5173

## 功能说明

1. **泛化检索**: 输入文学作品名称，系统自动爬取各主题模块概要
2. **深度检索**: 点击模块卡片，获取详细内容
3. **文档下载**: 将内容导出为 Word 文档

## 🚀 公网部署（Railway）

本项目支持一键部署到 Railway，实现公网访问。

### 快速部署

```bash
# 方式一：使用部署脚本
chmod +x deploy.sh
./deploy.sh

# 方式二：手动部署
# 1. 推送到 GitHub
git add .
git commit -m "Deploy to Railway"
git push

# 2. 在 Railway Dashboard 创建项目
# 访问 https://railway.app/dashboard
# 选择 "Deploy from GitHub repo"
```

### 部署文档

详细的部署说明请查看 [DEPLOY.md](DEPLOY.md)

### 部署优势

- ✅ **免费额度**: $5/月，足够小型项目
- ✅ **自动部署**: Git 推送即部署
- ✅ **HTTPS**: 自动配置 SSL 证书
- ✅ **数据持久化**: 支持 Volume 挂载
- ✅ **监控日志**: 内置日志和指标监控
