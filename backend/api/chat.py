from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict
import json
import uuid
import aiosqlite
from pathlib import Path

from models.schemas import ChatRequest
from chains.chat_chain import stream_chat
from auth import verify_api_key

router = APIRouter()

# 对话历史持久化 — SQLite
DB_PATH = Path(__file__).parent.parent / "conversations.db"
MAX_HISTORY_LEN = 20  # 最大历史消息数（每条含role+content）


async def _get_db() -> aiosqlite.Connection:
    """获取数据库连接"""
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            history TEXT NOT NULL DEFAULT '[]',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.commit()
    return db


async def _load_history(conversation_id: str) -> List[Dict]:
    """从数据库加载对话历史"""
    db = await _get_db()
    try:
        async with db.execute(
            "SELECT history FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return json.loads(row[0]) if row else []
    finally:
        await db.close()


async def _save_history(conversation_id: str, history: List[Dict]):
    """保存对话历史到数据库"""
    db = await _get_db()
    try:
        history_json = json.dumps(history, ensure_ascii=False)
        await db.execute(
            """INSERT INTO conversations (conversation_id, history, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(conversation_id) DO UPDATE SET
                 history = excluded.history,
                 updated_at = CURRENT_TIMESTAMP""",
            (conversation_id, history_json),
        )
        await db.commit()
    finally:
        await db.close()


@router.post("/chat/stream")
async def stream_chat_endpoint(
    request: ChatRequest,
    auth: dict = Depends(verify_api_key),
):
    """流式聊天端点

    通过 SSE (Server-Sent Events) 返回流式响应
    需要 X-API-Key 认证
    """

    async def generate():
        try:
            # 获取或创建对话 ID
            conversation_id = request.conversation_id or str(uuid.uuid4())

            # 从数据库加载对话历史
            history = await _load_history(conversation_id)

            # 流式生成响应
            full_response = ""
            async for chunk in stream_chat(
                query=request.query,
                page_content=request.page_content,
                url=request.url,
                title=request.title,
                model=request.model,
                conversation_history=history,
            ):
                full_response += chunk

                # 发送 SSE 事件
                data = {
                    "event": "message",
                    "content": chunk,
                    "conversation_id": conversation_id,
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            # 更新对话历史 — 同时保存 query 和 page_content
            history.append({
                "role": "user",
                "content": request.query,
                "page_content": request.page_content[:10000] if request.page_content else "",
            })
            history.append({
                "role": "assistant",
                "content": full_response,
            })

            # 限制历史长度
            if len(history) > MAX_HISTORY_LEN:
                history = history[-MAX_HISTORY_LEN:]

            # 持久化到数据库
            await _save_history(conversation_id, history)

            # 发送结束事件
            end_data = {
                "event": "message_end",
                "conversation_id": conversation_id,
            }
            yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"

        except ValueError as e:
            # 配置错误
            error_data = {"event": "error", "error": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        except Exception as e:
            # 其他错误
            error_data = {
                "event": "error",
                "error": "服务器内部错误",
                "detail": str(e),
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        },
    )


@router.post("/chat/clear/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    auth: dict = Depends(verify_api_key),
):
    """清除对话历史"""
    db = await _get_db()
    try:
        await db.execute(
            "DELETE FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        )
        await db.commit()
    finally:
        await db.close()
    return {"message": "对话历史已清除", "conversation_id": conversation_id}


@router.get("/chat/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    auth: dict = Depends(verify_api_key),
):
    """获取对话历史"""
    history = await _load_history(conversation_id)
    return {"conversation_id": conversation_id, "history": history}
