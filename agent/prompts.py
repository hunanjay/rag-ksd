"""
Agent 提示词模板
"""
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


def get_default_agent_prompt() -> ChatPromptTemplate:
    """获取默认的 Agent 提示词"""
    return ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的 AI 助手。你可以使用工具来回答问题。"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])


def get_rag_agent_prompt() -> ChatPromptTemplate:
    """获取 RAG Agent 提示词"""
    return ChatPromptTemplate.from_messages([
        (
            "system",
            """你是一个专门用于回答文档相关问题 AI 助手。
首先使用 rag_search 工具搜索相关文档内容，然后基于检索到的信息回答问题。
如果文档中没有相关信息，请明确说明。"""
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
