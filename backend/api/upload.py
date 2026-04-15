from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import uuid
import os
from pathlib import Path

from models.schemas import UploadResponse


router = APIRouter()

# 上传文件存储目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """上传文件端点

    支持上传图片文件，返回文件 ID 用于后续分析
    """

    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="只支持上传图片文件"
            )

        # 生成文件 ID
        file_id = str(uuid.uuid4())

        # 保存文件
        file_extension = Path(file.filename).suffix or ".jpg"
        file_path = UPLOAD_DIR / f"{file_id}{file_extension}"

        # 写入文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

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
async def get_file(file_id: str):
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
