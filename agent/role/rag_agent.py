# agent/role/rag_agent.py
"""
基于项目自有 RAG 能力的简单 Agent。

特点：
- RAG 检索逻辑完全复用 app.utils.rag_tools / db_tools
- 不依赖 langchain.agents 内部类型，避免版本兼容问题
- 继承 BaseAgent 获得默认流式支持
"""
from typing import Any, Dict, List
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.registry import register_agent
from agent.base_agent import BaseAgent
from app.utils.rag_tools import rag_search, get_document_details  # 仅作为工具使用

load_dotenv()


class RagAgent(BaseAgent):
    """一个简单的 RAG Agent 封装，提供 .invoke() 接口。"""

    def __init__(self, llm: ChatOpenAI, system_prompt: str) -> None:
        self.llm = llm
        self.system_prompt = system_prompt

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行一次对话。

        期望 inputs 结构：
        {
            "input": "用户问题",
            "chat_history": [HumanMessage/AIMessage, ...]  # 可选
        }
        """
        question: str = inputs.get("input", "")
        chat_history: List[Any] = inputs.get("chat_history") or []

        # 1. 使用 rag_search 工具检索相关文档
        retrieved = rag_search.run(question)

        # 2. 构造增强后的 system prompt
        if retrieved and retrieved != "未找到相关文档":
            enhanced_system = (
                f"{self.system_prompt}\n\n"
                f"以下是检索到的相关文档内容，请优先基于这些内容回答问题：\n"
                f"{retrieved}\n\n"
                f"如果文档中仍然没有相关信息，请明确说明。"
            )
        else:
            enhanced_system = (
                f"{self.system_prompt}\n\n"
                f"未检索到与用户问题高度相关的文档内容，"
                f"请基于你已有的知识进行回答，并说明未找到相关文档。"
            )

        # 3. 组装消息：system + 历史 + 当前问题
        messages: List[Any] = [SystemMessage(content=enhanced_system)]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=question))

        # 4. 调用 LLM
        response = self.llm.invoke(messages)
        if isinstance(response, AIMessage):
            answer = response.content
        else:
            answer = getattr(response, "content", str(response))

        return {
            "output": answer,
            "intermediate_steps": [
                {
                    "tool": "rag_search",
                    "input": question,
                    "output": retrieved,
                }
            ],
        }

    async def astream(self, inputs: Dict[str, Any]):
        """
        流式执行对话（异步生成器）。

        期望 inputs 结构：
        {
            "input": "用户问题",
            "chat_history": [HumanMessage/AIMessage, ...]  # 可选
        }
        """
        question: str = inputs.get("input", "")
        chat_history: List[Any] = inputs.get("chat_history") or []

        # 1. 使用 rag_search 工具检索相关文档
        retrieved = rag_search.run(question)

        # 2. 构造增强后的 system prompt
        if retrieved and retrieved != "未找到相关文档":
            enhanced_system = (
                f"{self.system_prompt}\n\n"
                f"以下是检索到的相关文档内容，请优先基于这些内容回答问题：\n"
                f"{retrieved}\n\n"
                f"如果文档中仍然没有相关信息，请明确说明。"
            )
        else:
            enhanced_system = (
                f"{self.system_prompt}\n\n"
                f"未检索到与用户问题高度相关的文档内容，"
                f"请基于你已有的知识进行回答，并说明未找到相关文档。"
            )

        # 3. 组装消息：system + 历史 + 当前问题
        messages: List[Any] = [SystemMessage(content=enhanced_system)]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=question))

        # 4. 流式调用 LLM
        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                content = chunk.content
                yield content


def create_rag_agent() -> RagAgent:
    """工厂函数：创建一个 RAG Agent 实例。"""
    llm = ChatOpenAI(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL"),
        temperature=0.0,
    )

    # 这里可以根据需要设置专门的 RAG 系统提示词
    system_prompt = (
        "你是一个专门用于回答文档相关问题的 AI 助手，名字叫小佳。"
        "你需要结合检索到的文档内容来回答用户的问题。"
    )

    return RagAgent(llm=llm, system_prompt=system_prompt)


# 模块导入时自动注册 RAG Agent
register_agent("rag", create_rag_agent)
