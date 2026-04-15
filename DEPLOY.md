# AI 网页助手部署指南

本文档介绍如何在不同设备上部署 AI 网页助手。

## 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

## 快速开始

### 1. 配置环境变量

复制后端配置模板：

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，配置 AI API Keys：

```bash
# 后端服务配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# AI 模型 API Keys（至少配置一个）
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 默认使用的模型
DEFAULT_MODEL=openai  # openai | deepseek | claude

# CORS 配置
ALLOWED_ORIGINS=chrome-extension://*,moz-extension://*
```

### 2. 启动服务

使用 Docker Compose 启动服务：

```bash
# 在项目根目录执行
docker-compose up -d
```

### 3. 验证服务

检查服务状态：

```bash
docker-compose ps
```

访问健康检查端点：

```bash
curl http://localhost:8000/health
```

预期返回：
```json
{"status": "healthy"}
```

### 4. 配置浏览器扩展

1. 打开 Chrome，访问 `chrome://extensions/`
2. 启用"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择项目根目录
5. 点击扩展图标，打开侧边栏
6. 点击右上角设置图标，配置后端服务地址：
   - 后端服务地址：`http://localhost:8000`（本地部署）
   - AI 模型：选择你配置的模型

## 不同设备部署

### Linux 服务器部署

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 克隆项目（如果是从 Git 仓库）
git clone <your-repo-url>
cd ai-extension

# 配置环境变量
cd backend
cp .env.example .env
nano .env  # 编辑配置

# 启动服务
cd ..
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### Windows 部署

1. 安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 打开 PowerShell 或 Command Prompt
3. 导航到项目目录
4. 配置环境变量（使用记事本或其他编辑器编辑 `backend/.env`）
5. 启动服务：
   ```powershell
   docker-compose up -d
   ```

### macOS 部署

1. 安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. 打开 Terminal
3. 导航到项目目录
4. 配置环境变量：
   ```bash
   cd backend
   cp .env.example .env
   nano .env  # 编辑配置
   ```
5. 启动服务：
   ```bash
   cd ..
   docker-compose up -d
   ```

## 远程部署

如果需要在远程服务器上部署，并在本地浏览器访问：

### 1. 服务器端配置

在远程服务器上部署服务（参考 Linux 服务器部署）。

### 2. 配置反向代理（推荐）

使用 Nginx 配置反向代理，启用 HTTPS：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

### 3. 修改 CORS 配置

在 `backend/.env` 中添加你的域名：

```bash
ALLOWED_ORIGINS=chrome-extension://*,moz-extension://*,https://your-domain.com
```

### 4. 浏览器扩展配置

在后端服务地址中填入：`https://your-domain.com`

## 常见问题

### Q1: 服务启动失败

**问题**：`docker-compose up` 报错

**解决方法**：
1. 检查 Docker 是否正常运行：`docker ps`
2. 查看服务日志：`docker-compose logs backend`
3. 检查端口 8000 是否被占用：`netstat -tlnp | grep 8000`

### Q2: 无法连接到后端服务

**问题**：浏览器扩展显示"服务器错误"

**解决方法**：
1. 检查后端服务是否运行：`curl http://localhost:8000/health`
2. 检查浏览器扩展配置的后端地址是否正确
3. 检查防火墙设置
4. 如果是远程部署，检查网络连接和反向代理配置

### Q3: API Key 配置错误

**问题**：扩展显示"未配置 API KEY"

**解决方法**：
1. 检查 `backend/.env` 文件中的 API Key 是否正确
2. 确保至少配置了一个 AI 模型的 API Key
3. 重启服务：`docker-compose restart backend`

### Q4: 图片上传失败

**问题**：截图后上传失败

**解决方法**：
1. 检查 `backend/uploads` 目录权限
2. 查看后端日志：`docker-compose logs backend`
3. 确保使用的 AI 模型支持图片分析（OpenAI 和 Claude 支持，DeepSeek 不支持）

### Q5: CORS 错误

**问题**：浏览器控制台显示 CORS 错误

**解决方法**：
1. 检查 `backend/.env` 中的 `ALLOWED_ORIGINS` 配置
2. 确保包含 `chrome-extension://*`
3. 重启服务：`docker-compose restart backend`

## 维护

### 查看日志

```bash
# 查看实时日志
docker-compose logs -f backend

# 查看最近 100 行日志
docker-compose logs --tail=100 backend
```

### 重启服务

```bash
# 重启后端服务
docker-compose restart backend

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 备份数据

```bash
# 备份上传的图片
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz backend/uploads/

# 备份配置
cp backend/.env backend/.env.backup-$(date +%Y%m%d)
```

## 性能优化

### 1. 增加内存限制

在 `docker-compose.yml` 中添加：

```yaml
services:
  backend:
    # ... 其他配置
    deploy:
      resources:
        limits:
          memory: 2G
```

### 2. 使用 GPU 加速（如果可用）

在 `docker-compose.yml` 中添加：

```yaml
services:
  backend:
    # ... 其他配置
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 3. 配置缓存

使用 Redis 缓存对话历史（需要额外配置 Redis 服务）。

## 安全建议

1. **不要将 `.env` 文件提交到版本控制**
2. **使用强密码和 API Key**
3. **启用 HTTPS**（生产环境必须）
4. **定期更新依赖**：`docker-compose pull`
5. **限制 API 访问频率**（可在后端添加速率限制）
6. **监控服务日志**，及时发现异常

## 技术支持

如果遇到问题：

1. 查看日志：`docker-compose logs backend`
2. 检查配置：`backend/.env`
3. 访问健康检查：`http://localhost:8000/health`
4. 查看 API 文档：`http://localhost:8000/docs`

## 更新日志

### v2.0.0
- 从 Dify API 迁移到 LangChain 架构
- 添加 Docker 容器化支持
- 支持多个 AI 模型（OpenAI、DeepSeek、Claude）
- 改进的流式响应处理
- 跨设备部署支持
