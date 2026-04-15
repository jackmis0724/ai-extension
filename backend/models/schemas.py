from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """聊天请求模型"""

    query: str = Field(..., description="用户查询内容")
    page_content: str = Field(default="", description="页面文本内容")
    url: str = Field(default="", description="页面 URL")
    title: str = Field(default="", description="页面标题")
    image_file_id: Optional[str] = Field(None, description="图片文件 ID")
    conversation_id: Optional[str] = Field(None, description="对话 ID")
    model: Optional[str] = Field(None, description="指定使用的模型")


class ChatResponse(BaseModel):
    """聊天响应模型"""

    content: str = Field(..., description="响应内容")
    conversation_id: Optional[str] = Field(None, description="对话 ID")
    done: bool = Field(default=False, description="是否结束")


class UploadResponse(BaseModel):
    """文件上传响应模型"""

    file_id: str = Field(..., description="文件 ID")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    size: int = Field(..., description="文件大小（字节）")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="错误详情")
