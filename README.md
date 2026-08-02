<div align="center">

# 📚 Literature-Retrieval

**基于 LLM 的文献检索与分析工具**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5+-646CFF?style=flat-square&logo=vite&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-Deploy-0B0D0E?style=flat-square&logo=railway&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

<br>

> 🔍 输入文学作品名称 → 自动检索泛化概要 → 深度挖掘详细内容 → 一键导出 Word 文档

[快速开始](#-快速启动) · [功能特性](#-功能特性) · [在线部署](#-在线部署) · [技术架构](#-技术架构) · [贡献指南](#-贡献指南)

</div>

---

## 📖 项目简介

Literature-Retrieval 是一款**基于大语言模型（LLM）的文学知识检索与展示系统**。系统支持双层权威信息抓取（泛化索引 + 深度挖掘）、分层本地知识库，并通过 React 前端提供交互式展示界面。

适用于学术研究、文献综述、文学分析等场景，帮助用户高效地获取和整理文献资料。

## ✨ 功能特性

| 功能 | 说明 |
|:---:|------|
| 🌐 **泛化检索** | 输入文学作品名称，自动爬取各主题模块概要 |
| 🔬 **深度检索** | 点击模块卡片，获取详细内容与分析 |
| 📄 **文档导出** | 将检索内容导出为 Word 文档，方便后续编辑 |
| 🧠 **本地知识库** | 基于 JSON 的分层本地知识库，支持 Dify API 扩展 |
| 🚀 **一键部署** | 支持 Railway 一键部署，自动配置 HTTPS |

## 🛠 技术栈

```
┌─────────────────────────────────────────────────┐
│                    Frontend                      │
│          React 18 + Vite 5 + TypeScript         │
├─────────────────────────────────────────────────┤
│                    Backend                       │
│           Python FastAPI + Scrapling            │
├─────────────────────────────────────────────────┤
│                  Knowledge Base                  │
│        本地 JSON + Dify API（可选扩展）          │
├─────────────────────────────────────────────────┤
│                   Deployment                     │
│         Railway · Docker · 自动 SSL              │
└─────────────────────────────────────────────────┘
```

## 🚀 快速启动

### 前置要求

- **Python** >= 3.10
- **Node.js** >= 18
- **Git**

### 1️⃣ 克隆仓库

```bash
git clone https://github.com/Delight0628/Literature-Retrieval.git
cd Literature-Retrieval
```

### 2️⃣ 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入 Dify 配置（可选）：

```env
DIFY_API_URL=https://api.dify.ai/v1
DIFY_API_KEY=your-api-key
DIFY_DATASET_ID=your-dataset-id
```

### 3️⃣ 启动后端服务

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

### 4️⃣ 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

### 5️⃣ 访问系统

打开浏览器访问 👉 **http://localhost:5173**

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t literature-retrieval .

# 运行容器
docker run -d -p 8002:8002 --env-file .env literature-retrieval
```

## ☁️ 在线部署

本项目支持一键部署到 [Railway](https://railway.app/)，实现公网访问。

### 方式一：脚本部署（推荐）

```bash
chmod +x deploy.sh
./deploy.sh
```

### 方式二：手动部署

```bash
# 1. 推送到 GitHub
git add .
git commit -m "Deploy to Railway"
git push

# 2. 在 Railway Dashboard 创建项目
# 访问 https://railway.app/dashboard
# 选择 "Deploy from GitHub repo"
# Railway 会自动检测 Dockerfile 并开始构建
```

### 部署优势

| 优势 | 详情 |
|:---:|------|
| 💰 | **免费额度** — $5/月，足够小型项目 |
| ⚡ | **自动部署** — Git 推送即部署 |
| 🔒 | **HTTPS** — 自动配置 SSL 证书 |
| 💾 | **数据持久化** — 支持 Volume 挂载 |
| 📊 | **监控日志** — 内置日志和指标监控 |

> 📄 详细的部署说明请查看 [DEPLOY.md](DEPLOY.md)

## 📂 项目结构

```
Literature-Retrieval/
├── backend/              # FastAPI 后端
│   ├── main.py           # 入口文件
│   └── requirements.txt  # Python 依赖
├── frontend/             # React 前端
│   ├── src/              # 源码目录
│   └── package.json      # Node.js 依赖
├── .env.example          # 环境变量模板
├── Dockerfile            # Docker 构建文件
├── deploy.sh             # 一键部署脚本
├── railway.json          # Railway 配置
└── DEPLOY.md             # 部署详细文档
```

## 🤝 贡献指南

欢迎所有形式的贡献！无论是提交 Bug 报告、功能建议还是代码 PR。

1. 🍴 Fork 本仓库
2. 🌿 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 💾 提交更改 (`git commit -m 'Add amazing feature'`)
4. 📤 推送分支 (`git push origin feature/amazing-feature`)
5. 📬 创建 Pull Request

## 📝 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 📮 联系方式

如有问题或建议，欢迎通过 [GitHub Issues](https://github.com/Delight0628/Literature-Retrieval/issues) 联系我们。

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！**

</div>
