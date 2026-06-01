# 🚀 Railway 部署指南

本项目使用 Railway 进行轻量级部署，支持免费额度（$5/月）。

## 前置条件

1. 注册 [Railway](https://railway.app/) 账号（支持 GitHub 登录）
2. 安装 [Railway CLI](https://docs.railway.app/reference/cli)（可选，命令行部署）

## 部署步骤

### 方式一：Git 部署（推荐）

1. **推送到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **在 Railway 创建项目**
   - 登录 [Railway Dashboard](https://railway.app/dashboard)
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库
   - Railway 会自动检测 Dockerfile 并开始构建

3. **配置环境变量**
   在 Railway 项目的 Variables 标签页添加：
   ```
   # Dify 配置（可选）
   DIFY_API_URL=https://api.dify.ai/v1
   DIFY_API_KEY=your-dify-api-key
   DIFY_DATASET_ID=your-dataset-id
   ```

4. **获取公网地址**
   - 部署完成后，点击 "Settings" → "Networking"
   - 点击 "Generate Domain" 获取免费的 `.railway.app` 域名
   - 或者绑定自己的域名

### 方式二：CLI 部署

1. **安装 Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **登录**
   ```bash
   railway login
   ```

3. **初始化项目**
   ```bash
   cd your-project
   railway init
   ```

4. **部署**
   ```bash
   railway up
   ```

5. **设置环境变量**
   ```bash
   railway variables set DIFY_API_KEY=your-key
   ```

6. **查看日志**
   ```bash
   railway logs
   ```

## 数据持久化

Railway 提供两种数据持久化方案：

### 方案一：使用 Railway Volume（推荐）

在 Railway Dashboard：
1. 进入项目 → Settings → Volumes
2. 点击 "Add Volume"
3. Mount Path 设置为 `/app/backend/data`
4. 重新部署

### 方案二：使用外部存储

如果需要更可靠的持久化，可以配置：
- AWS S3
- Cloudflare R2
- 阿里云 OSS

在 `.env` 中配置对应的访问密钥。

## 自定义域名

1. 在 Railway Dashboard → Settings → Networking → Custom Domain
2. 添加你的域名
3. 按提示配置 DNS：
   ```
   Type: CNAME
   Name: @ 或子域名
   Value: <your-project>.railway.app
   ```

## 监控和日志

- **实时日志**: Railway Dashboard → Deployments → 查看日志
- **指标监控**: Railway Dashboard → Metrics
- **健康检查**: `/api/health` 端点

## 常见问题

### Q: 构建失败怎么办？
A: 检查 Railway 构建日志，常见原因：
- 依赖安装失败
- Dockerfile 路径错误
- 内存不足（免费层限制 512MB）

### Q: 如何更新部署？
A: 推送到 GitHub 的部署分支（通常是 `main`），Railway 会自动重新部署。

### Q: 数据会丢失吗？
A: 如果没有配置 Volume，每次重新部署可能会丢失本地数据。建议：
1. 配置 Railway Volume
2. 或者将数据存储到外部数据库/OSS

### Q: 免费额度用完了怎么办？
A: Railway 免费额度为 $5/月，包含：
- 500 小时运行时间
- 1GB 内存
- 1GB 磁盘

超出后会暂停服务，下月重置。可以升级到付费计划。

## 本地测试

部署前可以本地测试 Docker 构建：

```bash
# 构建镜像
docker build -t literary-search .

# 运行容器
docker run -p 7000:7000 -e DIFY_API_KEY=your-key literary-search

# 访问 http://localhost:7000
```

## 性能优化

1. **启用缓存**: Railway 会自动缓存 Docker 层
2. **优化依赖**: 只安装必要的依赖
3. **使用 alpine 镜像**: 已在 Dockerfile 中使用 `python:3.11-slim`

## 安全建议

1. 不要将 API Key 提交到 Git
2. 使用 Railway 的环境变量功能
3. 定期轮换密钥
4. 启用 Railway 的访问控制