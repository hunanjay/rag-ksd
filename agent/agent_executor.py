"""
Agent 执行器
"""
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from typing import List, Optional
from app.config import settings
from app.agents.tools.base import get_tools


def create_agent_executor(
    tools: Optional[List[Tool]] = None,
    llm: Optional[ChatOpenAI] = None,
    tool_names: Optional[List[str]] = None,
    verbose: Optional[bool] = None,
    max_iterations: Optional[int] = None,
    max_execution_time: Optional[int] = None,
) -> AgentExecutor:
    """
    创建 Agent 执行器
    
    Args:
        tools: 工具列表，如果不提供则根据 tool_names 获取
        llm: LLM 实例，如果不提供则使用默认的
        tool_names: 工具名称列表，如果 tools 为 None 则使用此参数
        verbose: 是否显示详细日志
        max_iterations: 最大迭代次数
        max_execution_time: 最大执行时间（秒）
    
    Returns:
        AgentExecutor 实例
    """
    if tools is None:
        tools = get_tools(tool_names)
    
    if llm is None:
        llm = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            streaming=True,
            temperature=0,
        )
    
    if verbose is None:
        verbose = settings.VERBOSE
    
    if max_iterations is None:
        max_iterations = settings.MAX_ITERATIONS
    
    # 创建提示词模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的 AI 助手。你可以使用工具来回答问题。"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 创建 Agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    
    # 创建 Agent 执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        max_iterations=max_iterations,
        max_execution_time=max_execution_time,
        handle_parsing_errors=True,
    )
    
    return agent_executor
