from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from collections import defaultdict
import time

from config import settings
from api import chat, upload
from auth import init_db

# 速率限制：内存计数器
_request_counts: dict[str, list[float]] = defaultdict(list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print(f"🚀 AI 网页助手后端服务启动")
    print(f"📡 监听地址: http://{settings.backend_host}:{settings.backend_port}")
    print(f"🤖 默认模型: {settings.default_model}")

    # 初始化数据库
    await init_db()
    print(f"🔑 API Key数据库已初始化")

    yield

    # 关闭时执行
    print("👋 AI 网页助手后端服务关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="AI 网页助手 API",
    description="基于 LangChain 的 AI 网页助手后端服务",
    version="3.0.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 速率限制中间件
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """基于API Key + IP的速率限制"""
    # 健康检查不限速
    if request.url.path == "/health":
        return await call_next(request)

    # 预检请求不限速
    if request.method == "OPTIONS":
        return await call_next(request)

    api_key = request.headers.get("x-api-key", f"ip:{request.client.host}")
    now = time.time()
    window = 60  # 1分钟窗口

    # 清理过期记录
    _request_counts[api_key] = [
        t for t in _request_counts[api_key] if now - t < window
    ]

    if len(_request_counts[api_key]) >= settings.rate_limit_per_minute:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "retry_after": 60},
        )

    _request_counts[api_key].append(now)
    return await call_next(request)


# 注册路由
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(upload.router, prefix="/api", tags=["upload"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI 网页助手 API",
        "version": "3.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
