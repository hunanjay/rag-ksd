from fastapi import FastAPI
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


class ChatRequest(BaseModel):
    q: str
    session_id: Optional[str] = None  # 会话ID，如果为空则创建新会话


class ChatResponse(BaseModel):
    answer: str
    session_id: str  # 返回会话ID，前端需要保存并下次请求时传递


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