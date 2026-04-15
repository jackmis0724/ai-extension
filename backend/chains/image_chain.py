from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from typing import Optional
import base64

from config import settings


def get_vision_llm(model: Optional[str] = None):
    """获取支持视觉的 LLM 实例"""

    model_name = model or settings.default_model

    if model_name == "openai":
        if not settings.openai_api_key:
            raise ValueError("未配置 OPENAI_API_KEY")
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.7,
            streaming=True,
        )
    elif model_name == "deepseek":
        # DeepSeek 目前不支持视觉
        raise ValueError("DeepSeek 模型不支持图片分析，请使用 OpenAI 或 Claude")
    elif model_name == "claude":
        if not settings.anthropic_api_key:
            raise ValueError("未配置 ANTHROPIC_API_KEY")
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.7,
            max_tokens=4096,
        )
    else:
        raise ValueError(f"不支持的模型: {model_name}")


def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为 base64

    Args:
        image_path: 图片文件路径

    Returns:
        base64 编码的图片数据
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def analyze_image(
    image_data: bytes,
    query: str = "请分析这张图片",
    model: Optional[str] = None,
):
    """分析图片

    Args:
        image_data: 图片二进制数据
        query: 用户查询
        model: 模型名称

    Yields:
        流式响应内容
    """

    llm = get_vision_llm(model)
    model_name = model or settings.default_model

    # 编码图片
    base64_image = base64.b64encode(image_data).decode("utf-8")

    # 构建消息
    if model_name == "openai":
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": query,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "auto",
                    },
                },
            ]
        )
    elif model_name == "claude":
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": query,
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image,
                    },
                },
            ]
        )
    else:
        raise ValueError(f"不支持的模型: {model_name}")

    # 创建链
    chain = llm | StrOutputParser()

    # 流式输出
    async for chunk in chain.astream([message]):
        if chunk:
            yield chunk
