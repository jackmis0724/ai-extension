from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional
import uuid
import os
import time
from pathlib import Path

from models.schemas import UploadResponse
from auth import verify_api_key
from config import settings

router = APIRouter()

# 上传文件存储目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def cleanup_expired_uploads():
    """清理过期的上传文件"""
    expiry_seconds = settings.upload_expiry_hours * 3600
    now = time.time()
    cleaned = 0
    for f in UPLOAD_DIR.iterdir():
        if f.is_file() and (now - f.stat().st_mtime) > expiry_seconds:
            f.unlink()
            cleaned += 1
    return cleaned


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    auth: dict = Depends(verify_api_key),
):
    """上传文件端点

    支持上传图片文件，返回文件 ID 用于后续分析
    需要 X-API-Key 认证
    """

    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="只支持上传图片文件"
            )

        # 读取文件内容
        content = await file.read()

        # 验证文件大小
        if len(content) > settings.max_upload_size:
            max_mb = settings.max_upload_size / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制（最大 {max_mb:.0f}MB）",
            )

        # 生成文件 ID
        file_id = str(uuid.uuid4())

        # 保存文件
        file_extension = Path(file.filename).suffix or ".jpg"
        file_path = UPLOAD_DIR / f"{file_id}{file_extension}"

        with open(file_path, "wb") as f:
            f.write(content)

        # 顺便清理过期文件（非阻塞，失败不影响上传）
        try:
            await cleanup_expired_uploads()
        except Exception:
            pass

        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_path=str(file_path),
            size=len(content),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"文件上传失败: {str(e)}"
        )


@router.get("/upload/{file_id}")
async def get_file(
    file_id: str,
    auth: dict = Depends(verify_api_key),
):
    """获取上传的文件

    返回文件的二进制数据
    """

    # 查找文件
    matching_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))

    if not matching_files:
        raise HTTPException(status_code=404, detail="文件不存在")

    file_path = matching_files[0]

    # 读取并返回文件
    with open(file_path, "rb") as f:
        content = f.read()

    from fastapi.responses import Response

    # 根据 file_extension 设置 content type
    content_type = "image/jpeg"  # 默认
    if file_path.suffix == ".png":
        content_type = "image/png"
    elif file_path.suffix == ".gif":
        content_type = "image/gif"
    elif file_path.suffix == ".webp":
        content_type = "image/webp"

    return Response(content=content, media_type=content_type)
