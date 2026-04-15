from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import json
import uuid

from models.schemas import ChatRequest
from chains.chat_chain import stream_chat


router = APIRouter()


# 内存中存储对话历史（生产环境应该使用数据库）
conversation_histories: Dict[str, List] = {}


@router.post("/chat/stream")
async def stream_chat_endpoint(request: ChatRequest):
    """流式聊天端点

    通过 SSE (Server-Sent Events) 返回流式响应
    """

    async def generate():
        try:
            # 获取或创建对话 ID
            conversation_id = request.conversation_id or str(uuid.uuid4())

            # 获取对话历史
            history = conversation_histories.get(conversation_id, [])

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

            # 更新对话历史
            if conversation_id not in conversation_histories:
                conversation_histories[conversation_id] = []

            conversation_histories[conversation_id].append(
                {"role": "user", "content": request.query}
            )
            conversation_histories[conversation_id].append(
                {"role": "assistant", "content": full_response}
            )

            # 限制历史长度
            if len(conversation_histories[conversation_id]) > 20:
                conversation_histories[conversation_id] = conversation_histories[
                    conversation_id
                ][-20:]

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
async def clear_conversation(conversation_id: str):
    """清除对话历史"""

    if conversation_id in conversation_histories:
        del conversation_histories[conversation_id]

    return {"message": "对话历史已清除", "conversation_id": conversation_id}


@router.get("/chat/history/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """获取对话历史"""

    history = conversation_histories.get(conversation_id, [])
    return {"conversation_id": conversation_id, "history": history}
