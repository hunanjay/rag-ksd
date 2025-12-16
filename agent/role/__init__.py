"""
agent.role 包

用于放置不同“角色”的 Agent 实现，例如：
- rag_agent.py  : 基于 RAG 的检索增强 Agent
- langchain_agent.py : 使用 LangChain 官方 Agent 的通用 Agent

各文件内部负责：
- 定义自己的 prompt / 工厂函数
- 在模块导入时调用 register_agent() 完成自注册
"""

