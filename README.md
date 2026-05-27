# 文学知识检索与展示系统

支持双层权威信息抓取（泛化索引 + 深度挖掘）、分层本地知识库、React 前端交互展示。

## 技术栈

- **爬虫**: Scrapling
- **知识库**: RAGFlow API
- **后端**: Python FastAPI
- **前端**: React + Vite

## 快速启动

### 1. 配置环境变量

编辑 `.env` 文件，填入 RAGFlow 的 API 地址和密钥：

```
RAGFLOW_API_URL=http://your-ragflow-instance:9380
RAGFLOW_API_KEY=your-api-key
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
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
