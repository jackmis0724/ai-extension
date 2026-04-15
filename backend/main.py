from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from api import chat, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print(f"🚀 AI 网页助手后端服务启动")
    print(f"📡 监听地址: http://{settings.backend_host}:{settings.backend_port}")
    print(f"🤖 默认模型: {settings.default_model}")

    yield

    # 关闭时执行
    print("👋 AI 网页助手后端服务关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="AI 网页助手 API",
    description="基于 LangChain 的 AI 网页助手后端服务",
    version="2.0.0",
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

# 注册路由
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(upload.router, prefix="/api", tags=["upload"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI 网页助手 API",
        "version": "2.0.0",
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
