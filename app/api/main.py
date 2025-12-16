from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Optional, Dict, AsyncIterator
import os
import uuid
import json
from dotenv import load_dotenv
from app.utils.template_loader import get_system_message_from_template
from agent import get_agent, list_agents

load_dotenv()

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatOpenAI(
    model_name="gpt-4o",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_BASE_URL")
)

# 加载系统提示词模板
try:
    system_prompt = get_system_message_from_template("rag_instructions.j2")
except Exception as e:
    # 如果模板加载失败，使用默认提示词
    print(f"警告: 无法加载提示词模板: {e}")
    system_prompt = "你是一个有用的 AI 助手。"

# 在内存中存储对话历史：{session_id: [messages]}
conversation_history: Dict[str, List] = {}

# Agent 对话历史存储：{session_id: [messages]}
agent_conversation_history: Dict[str, List] = {}


class ChatRequest(BaseModel):
    q: str
    session_id: Optional[str] = None  # 会话ID，如果为空则创建新会话


class ChatResponse(BaseModel):
    answer: str
    session_id: str  # 返回会话ID，前端需要保存并下次请求时传递


class AgentChatRequest(BaseModel):
    q: str
    session_id: Optional[str] = None  # 会话ID，如果为空则创建新会话
    agent_name: Optional[str] = None  # Agent 名称，如果不提供则使用路径参数


@app.get("/health")
async def health() -> Dict[str, object]:
    """简单健康检查接口，用于前端检测后端状态。"""
    return {
        "status": "ok",
        "agents": list_agents(),
    }


async def stream_chat(request: ChatRequest) -> AsyncIterator[str]:
    """流式生成聊天响应"""
    # 如果没有提供 session_id，创建一个新的
    if not request.session_id:
        session_id = str(uuid.uuid4())
    else:
        session_id = request.session_id
    
    # 获取或初始化该会话的对话历史
    if session_id not in conversation_history:
        conversation_history[session_id] = []
        # 如果是新会话，添加系统消息
        conversation_history[session_id].append(SystemMessage(content=system_prompt))
    
    # 添加用户消息到历史记录
    conversation_history[session_id].append(HumanMessage(content=request.q))
    
    # 先发送 session_id
    yield f"data: {json.dumps({'type': 'session_id', 'data': session_id})}\n\n"
    
    # 收集完整的响应内容
    full_content = ""
    
    # 流式调用 LLM（包含系统消息和对话历史）
    async for chunk in llm.astream(conversation_history[session_id]):
        if hasattr(chunk, 'content') and chunk.content:
            content = chunk.content
            full_content += content
            # 发送每个 chunk
            yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"
    
    # 添加完整的 AI 响应到历史记录
    conversation_history[session_id].append(AIMessage(content=full_content))
    
    # 发送完成标志
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@app.post("/chat")
async def chat(request: ChatRequest):
    """流式聊天接口"""
    return StreamingResponse(
        stream_chat(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


@app.delete("/chat/{session_id}")
async def clear_history(session_id: str):
    """清除指定会话的对话历史"""
    if session_id in conversation_history:
        del conversation_history[session_id]
        return {"message": "对话历史已清除"}
    return {"message": "会话不存在"}


@app.post("/chat/run/{agent_name}/v1")
async def chat_with_agent(agent_name: str, request: AgentChatRequest):
    """
    使用指定的 Agent 进行对话（非流式）。

    Args:
        agent_name: Agent 名称（如 "rag"）
        request: 聊天请求，包含问题和可选的 session_id / agent_name
    """
    try:
        # 请求体中指定的 agent_name 优先级更高
        actual_agent_name = request.agent_name or agent_name

        # 获取 agent 实例（由 registry + 各 role 模块自动注册）
        agent_instance = get_agent(actual_agent_name)

        # 管理会话历史
        session_id = request.session_id or str(uuid.uuid4())
        if session_id not in agent_conversation_history:
            agent_conversation_history[session_id] = []

        # 调用 agent 的 invoke 接口
        result = agent_instance.invoke(
            {
                "input": request.q,
                "chat_history": agent_conversation_history[session_id],
            }
        )

        # 更新历史
        agent_conversation_history[session_id].extend(
            [
                HumanMessage(content=request.q),
                AIMessage(content=result.get("output", "")),
            ]
        )

        return {
            "answer": result.get("output", ""),
            "session_id": session_id,
            "agent_name": actual_agent_name,
            "intermediate_steps": result.get("intermediate_steps", []),
        }

    except ValueError as e:
        # Agent 未注册
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 其他错误
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")


@app.get("/chat/agents")
async def list_available_agents():
    """列出所有已注册的 Agent 名称"""
    return {"agents": list_agents()}


@app.delete("/chat/agent/{session_id}")
async def clear_agent_history(session_id: str):
    """清除指定会话的 Agent 对话历史"""
    if session_id in agent_conversation_history:
        del agent_conversation_history[session_id]
        return {"message": "Agent 对话历史已清除"}
    return {"message": "会话不存在"}
