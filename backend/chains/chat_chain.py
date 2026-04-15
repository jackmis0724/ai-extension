from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from typing import Optional, List

from config import settings


def get_llm(model: Optional[str] = None):
    """根据模型名称获取对应的 LLM 实例"""

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
        if not settings.deepseek_api_key:
            raise ValueError("未配置 DEEPSEEK_API_KEY")
        return ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
            temperature=0.7,
            streaming=True,
        )
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


def create_chat_chain(
    model: Optional[str] = None,
    conversation_history: Optional[List] = None,
):
    """创建聊天链

    Args:
        model: 模型名称
        conversation_history: 对话历史

    Returns:
        LangChain 链实例
    """

    llm = get_llm(model)

    # 构建系统提示
    system_prompt = """你是一个智能 AI 助手，专门帮助用户分析网页内容。

你的任务：
1. 仔细阅读用户提供的页面内容和上下文信息
2. 理解用户的问题和需求
3. 基于页面内容提供准确、有用的回答
4. 如果页面内容不足以回答问题，请明确告知
5. 回答要简洁明了，重点突出

注意事项：
- 页面内容可能包含大量文本，需要筛选关键信息
- 保持客观中立的态度
- 如果用户询问代码或技术问题，提供清晰的解释
- 可以适当使用格式（如列表、代码块）来组织回答
"""

    # 构建提示模板
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="history", optional=True),
            (
                "human",
                """页面信息：
- 标题：{title}
- URL：{url}
- 页面内容：
{page_content}

用户问题：{query}""",
            ),
        ]
    )

    # 创建链
    chain = prompt | llm | StrOutputParser()

    return chain


async def stream_chat(
    query: str,
    page_content: str = "",
    url: str = "",
    title: str = "",
    model: Optional[str] = None,
    conversation_history: Optional[List] = None,
):
    """流式聊天

    Args:
        query: 用户查询
        page_content: 页面内容
        url: 页面 URL
        title: 页面标题
        model: 模型名称
        conversation_history: 对话历史

    Yields:
        流式响应内容
    """

    chain = create_chat_chain(model=model, conversation_history=conversation_history)

    # 构建输入
    inputs = {
        "query": query,
        "page_content": page_content[:10000] if page_content else "",  # 限制长度
        "url": url,
        "title": title,
    }

    if conversation_history:
        inputs["history"] = conversation_history

    # 流式输出
    async for chunk in chain.astream(inputs):
        if chunk:
            yield chunk
