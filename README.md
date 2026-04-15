# AI 网页助手

基于 LangChain 的 Chrome 浏览器扩展，提供智能网页内容分析和图片识别功能。

## 功能特性

- 🤖 **多模型支持**：集成 OpenAI、DeepSeek、Claude 等主流 AI 模型
- 📄 **页面分析**：自动提取和分析当前网页内容
- 📸 **截图识别**：支持全屏截图和局部截图，AI 分析图片内容
- 💬 **流式对话**：实时的打字机效果，提升交互体验
- 🔄 **对话历史**：自动保存对话上下文，支持多轮对话
- 🐳 **容器化部署**：Docker 一键部署，跨平台兼容
- 🔒 **安全可控**：使用官方 AI API，数据安全可控

## 技术架构

```
Chrome Extension (前端)
       ↓ HTTPS/HTTP
FastAPI + LangChain (后端 Docker 容器)
       ↓
官方 AI API (OpenAI/DeepSeek/Claude)
```

### 技术栈

- **前端**：Chrome Extension (Manifest V3)、Vanilla JavaScript
- **后端**：FastAPI、LangChain、Pydantic
- **AI 模型**：OpenAI GPT-4o-mini、DeepSeek Chat、Claude 3.5 Sonnet
- **部署**：Docker、Docker Compose
- **通信**：SSE (Server-Sent Events)

## 快速开始

### 前置要求

- Chrome 或 Edge 浏览器
- Docker 20.10+
- Docker Compose 2.0+
- 至少一个 AI 模型的 API Key

### 安装步骤

#### 1. 克隆项目

```bash
git clone <your-repo-url>
cd ai-extension
```

#### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，配置 API Keys：

```bash
# 至少配置一个 API Key
OPENAI_API_KEY=your_openai_api_key_here
# 或
DEEPSEEK_API_KEY=your_deepseek_api_key_here
# 或
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### 3. 启动后端服务

```bash
cd ..
docker-compose up -d
```

#### 4. 加载浏览器扩展

1. 打开 Chrome，访问 `chrome://extensions/`
2. 启用"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择项目根目录
5. 扩展安装完成！

#### 5. 配置扩展

1. 点击浏览器工具栏中的扩展图标
2. 打开侧边栏
3. 点击右上角设置图标
4. 配置：
   - 后端服务地址：`http://localhost:8000`
   - AI 模型：选择你配置的模型

## 使用方法

### 文本对话

1. 在任意网页打开扩展
2. 在输入框中输入问题
3. 按下 Enter 发送
4. AI 会结合页面内容回答你的问题

### 截图分析

#### 全屏截图

点击侧边栏底部的 📷 按钮即可截取当前页面。

#### 局部截图

点击 ✂️ 按钮，然后在页面上拖拽选择区域。

### 多轮对话

扩展会自动保存对话历史，支持上下文关联的多轮对话。

## 项目结构

```
ai-extension/
├── backend/                 # 后端服务
│   ├── api/                # API 路由
│   │   ├── chat.py        # 聊天端点
│   │   └── upload.py      # 上传端点
│   ├── chains/            # LangChain 链
│   │   ├── chat_chain.py  # 聊天链
│   │   └── image_chain.py # 图片分析链
│   ├── models/            # 数据模型
│   │   └── schemas.py     # Pydantic 模型
│   ├── uploads/           # 上传文件存储
│   ├── main.py           # FastAPI 主应用
│   ├── config.py         # 配置管理
│   ├── Dockerfile        # Docker 配置
│   └── requirements.txt   # Python 依赖
├── background.js         # 后台脚本
├── sidepanel.html        # 侧边栏界面
├── sidepanel.js          # 侧边栏逻辑
├── options.html          # 配置界面
├── options.js            # 配置逻辑
├── inject_crop.js        # 截图注入脚本
├── manifest.json         # 扩展清单
├── marked.min.js         # Markdown 解析库
├── docker-compose.yml    # Docker Compose 配置
├── DEPLOY.md            # 部署文档
├── README.md            # 本文件
└── CLAUDE.md            # Claude Code 指南
```

## 配置说明

### 后端配置 (backend/.env)

```bash
# 服务配置
BACKEND_HOST=0.0.0.0          # 监听地址
BACKEND_PORT=8000             # 监听端口

# AI 模型 API Keys
OPENAI_API_KEY=sk-xxx         # OpenAI API Key
DEEPSEEK_API_KEY=sk-xxx      # DeepSeek API Key
ANTHROPIC_API_KEY=sk-ant-xxx # Anthropic API Key

# 默认模型
DEFAULT_MODEL=openai          # openai | deepseek | claude

# CORS 配置
ALLOWED_ORIGINS=chrome-extension://*,moz-extension://*
```

### 扩展配置

在浏览器扩展配置页面可以设置：
- 后端服务地址
- AI 模型选择

## API 文档

启动服务后，访问 `http://localhost:8000/docs` 查看完整的 API 文档。

### 主要端点

- `POST /api/chat/stream` - 流式聊天
- `POST /api/upload` - 上传文件
- `GET /health` - 健康检查

## 部署指南

详细的部署指南请参考 [DEPLOY.md](DEPLOY.md)。

支持的部署方式：
- 本地开发（Docker Compose）
- Linux 服务器
- Windows
- macOS
- 云服务器（带反向代理）

## 开发指南

### 本地开发后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动开发服务器
uvicorn main:app --reload --port 8000
```

### 开发前端扩展

1. 修改前端代码后，在 `chrome://extensions/` 刷新扩展
2. 右键点击侧边栏选择"检查"进行调试
3. 右键点击扩展图标选择"检查弹出内容"调试后台脚本

### 代码规范

- Python 遵循 PEP 8 规范
- JavaScript 使用现代 ES6+ 语法
- 添加必要的注释和文档字符串

## 常见问题

### Q: 扩展无法连接到后端服务？

A: 检查：
1. 后端服务是否正常运行：`curl http://localhost:8000/health`
2. 扩展配置中的后端地址是否正确
3. 浏览器控制台是否有 CORS 错误

### Q: 图片上传失败？

A: 确保使用的 AI 模型支持图片分析：
- ✅ OpenAI (GPT-4o-mini) - 支持
- ✅ Claude (3.5 Sonnet) - 支持
- ❌ DeepSeek - 不支持（纯文本模型）

### Q: 为什么使用 DeepSeek 模型时无法截图？

A: DeepSeek 是纯语言模型，不支持图片分析功能。当你使用 DeepSeek 时：
- 截图按钮会被点击并显示提醒
- 提示用户切换到支持图片分析的模型
- 你仍然可以进行文本对话

### Q: 如何切换 AI 模型？

A: 在扩展配置页面选择不同的模型，或在后端 `.env` 中修改 `DEFAULT_MODEL`。

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - 强大的 LLM 应用开发框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
- [OpenAI](https://openai.com/) - GPT-4o-mini API
- [DeepSeek](https://www.deepseek.com/) - DeepSeek Chat API
- [Anthropic](https://www.anthropic.com/) - Claude API

## 更新日志

### v2.0.0 (2024-04-08)

- 🔄 从 Dify API 迁移到 LangChain 架构
- 🐳 添加 Docker 容器化支持
- 🤖 支持多个 AI 模型（OpenAI、DeepSeek、Claude）
- 💬 改进的流式响应处理
- 📸 优化的图片上传和分析功能
- 🚀 跨设备部署支持
- 📝 完善的部署文档

### v1.0.0

- 初始版本
- 基于 Dify API
- 基本聊天和截图功能

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
