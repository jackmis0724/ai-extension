"""API Key认证模块 — SQLite存储，FastAPI依赖注入"""

import aiosqlite
from pathlib import Path
from fastapi import Header, HTTPException

DB_PATH = Path(__file__).parent / "api_keys.db"


async def init_db() -> None:
    """初始化数据库，创建api_keys表"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rate_limit INTEGER DEFAULT 60,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def verify_api_key(x_api_key: str = Header(None)) -> dict:
    """验证API Key，返回key信息字典

    Returns:
        {"key": str, "name": str, "rate_limit": int}

    Raises:
        HTTPException 401: Key缺失或无效
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT key, name, rate_limit FROM api_keys WHERE key = ? AND is_active = 1",
            (x_api_key,),
        ) as cursor:
            row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    return {"key": row[0], "name": row[1], "rate_limit": row[2]}