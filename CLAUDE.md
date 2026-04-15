# CLAUDE.md

始终使用中文与我交流

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Chrome Manifest V3 浏览器扩展（AI网页助手），基于 LangChain 架构提供 AI 聊天、网页内容分析和图片识别功能。后端使用 FastAPI + Docker 容器化部署，支持 OpenAI、DeepSeek、Claude 等多个 AI 模型。

## 核心架构

### 系统架构

```
Chrome Extension (前端)
       ↓ HTTPS/HTTP
FastAPI + LangChain (后端 Docker 容器)
       ↓
官方 AI API (OpenAI/DeepSeek/Claude)
```

### 消息流与页面上下文

用户发送消息时，扩展执行以下流程：
1. 通过 `chrome.scripting.executeScript(() => document.body.innerText)` 获取当前标签页的页面内容
2. 将页面内容、URL、标题等上下文信息发送给后端 `/api/chat/stream` 端点
3. 后端使用 LangChain 构建对话链，将页面内容作为系统提示的一部分
4. 通过 SSE (Server-Sent Events) 返回流式响应
5. 前端解析 SSE 事件并实时更新 UI
6. 对话 ID 存储在 `chrome.storage.session` 中，切换标签页时重置

### 流式响应解析

侧边栏处理来自后端的 SSE 事件：
1. **message 事件**：AI 响应内容，累积显示
2. **thought 事件**：思考过程（如果后端支持），显示在可折叠的思考框中
3. **error 事件**：错误信息，显示给用户
4. **message_end 事件**：对话结束，保存 conversation_id

### 截图流程

- **全屏截图**：直接调用 `chrome.tabs.captureVisibleTab()`
- **局部截图**：`inject_crop.js` 创建覆盖层，跟踪鼠标拖拽，发送坐标回主脚本 → 捕获全屏截图 → Canvas 裁剪到选中区域（考虑 `window.devicePixelRatio`）
- **图片上传**：将截图上传到后端 `/api/upload` 端点，获得 file_id
- **图片分析**：file_id 包含在聊天请求中，后端使用支持视觉的 LLM 进行分析

### 存储架构

- **chrome.storage.local**：持久化配置（后端服务地址、AI 模型选择）
- **chrome.storage.session**：临时聊天历史和对话状态（浏览器关闭时清除）
- **后端内存**：对话历史存储在后端内存中（生产环境应使用数据库）

## 后端架构

### 目录结构

```
backend/
├── main.py                 # FastAPI 主应用
├── config.py               # 配置管理（环境变量）
├── chains/                 # LangChain 链定义
│   ├── chat_chain.py       # 主聊天链
│   └── image_chain.py      # 图片分析链
├── api/                    # API 路由
│   ├── chat.py             # 聊天端点（SSE 流式）
│   └── upload.py           # 文件上传端点
├── models/                 # Pydantic 模型
│   └── schemas.py          # 请求/响应数据模型
├── uploads/               # 上传文件存储目录
├── requirements.txt       # Python 依赖
└── .env                   # 环境变量配置
```

### LangChain 链设计

**chat_chain.py**：
- 使用 `ChatPromptTemplate` 构建提示，包含系统消息和用户消息
- 系统消息定义 AI 助手的角色和任务
- 用户消息包含页面内容（page_content）、URL、标题和用户查询
- 支持对话历史上下文
- 支持多个 LLM 提供商（OpenAI、DeepSeek、Claude）

**image_chain.py**：
- 使用支持视觉的 LLM（OpenAI GPT-4o-mini 或 Claude 3.5 Sonnet）
- 将图片编码为 base64
- 构建包含图片的 HumanMessage
- 流式返回分析结果

### 环境变量配置

关键环境变量在 `backend/.env` 中配置：
- `OPENAI_API_KEY`：OpenAI API 密钥
- `DEEPSEEK_API_KEY`：DeepSeek API 密钥
- `ANTHROPIC_API_KEY`：Anthropic API 密钥
- `DEFAULT_MODEL`：默认使用的模型（openai/deepseek/claude）
- `BACKEND_HOST` 和 `BACKEND_PORT`：服务监听地址和端口
- `ALLOWED_ORIGINS`：CORS 允许的来源

## 开发指南

### 加载扩展

在 Chrome 中访问 `chrome://extensions/`，启用"开发者模式"，点击"加载已解压的扩展程序"，选择此目录。

### 启动后端服务

**使用 Docker Compose（推荐）**：
```bash
docker-compose up -d
```

**本地开发**：
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 调试方法

- **侧边栏**：右键 → 检查
- **后台 Service Worker**：chrome://extensions/ → "Service worker" 链接
- **后端 API**：访问 http://localhost:8000/docs 查看 API 文档
- **后端日志**：`docker-compose logs -f backend` 或查看终端输出

### 修改代码后

1. **前端**：在 chrome://extensions/ 刷新扩展，关闭并重新打开侧边栏
2. **后端**：Docker 模式下执行 `docker-compose restart backend`，本地开发模式会自动重载

## 依赖项

### 前端
- **marked.min.js**：Markdown 解析（已打包）

### 后端
主要依赖见 `backend/requirements.txt`：
- FastAPI：Web 框架
- LangChain：LLM 应用框架
- langchain-openai：OpenAI 集成
- langchain-anthropic：Anthropic 集成
- Pydantic：数据验证
- Uvicorn：ASGI 服务器

## API 集成

### 主要端点

- `POST /api/chat/stream`：流式聊天（SSE）
  - 请求体：query, page_content, url, title, model, conversation_id, image_file_id
  - 响应：SSE 流，包含 message, thought, error, message_end 事件

- `POST /api/upload`：文件上传
  - 请求：multipart/form-data，包含 file 字段
  - 响应：file_id, filename, file_path, size

- `GET /health`：健康检查

## 重要实现细节

### CORS 配置

后端配置 CORS 允许浏览器扩展访问，在 `backend/config.py` 和 `backend/.env` 中配置。

### 对话上下文管理

- 前端：使用 `chrome.storage.session` 保存 conversation_id 和 savedUrl
- 后端：使用内存字典存储对话历史（生产环境应使用 Redis 或数据库）
- 切换标签页时自动重置对话

### 图片处理

- 前端将 dataURL 转换为 Blob 上传
- 后端保存到 `backend/uploads` 目录
- 图片分析时编码为 base64 发送给 LLM

### 错误处理

- 前端：显示错误消息，重置发送按钮状态
- 后端：捕获异常，通过 SSE error 事件返回
- 日志：后端记录详细错误信息便于调试

## 部署

详细的部署指南请参考 `DEPLOY.md`。

快速部署：
```bash
# 配置环境变量
cd backend
cp .env.example .env
# 编辑 .env 文件

# 启动服务
cd ..
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

## 注意事项

1. **API Key 安全**：不要将 `.env` 文件提交到版本控制，API Key 仅在后端配置
2. **模型支持**：图片分析仅支持 OpenAI 和 Claude，DeepSeek 不支持视觉功能
3. **内存管理**：后端对话历史存储在内存中，重启服务会丢失
4. **CORS 配置**：远程部署时需要配置正确的 ALLOWED_ORIGINS
5. **SSE 超时**：长时间对话可能遇到超时，可调整 Nginx 或浏览器设置
