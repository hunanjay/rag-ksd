"""
Agents 模块入口

使用注册中心模式：
- 新增 Agent 只需在各自的 {name}_agent.py 中调用 register_agent() 注册
- 不需要修改 main.py
- 每个 Agent 的 prompt 在各自模块内管理，互不影响
"""

from .registry import register_agent, get_agent, list_agents

# 导入所有内置 agent 角色以触发自动注册。
# 注意：导入顺序很重要，确保所有内置 agent 都完成 register_agent 调用。
from .role import rag_agent  # noqa: F401

__all__ = [
    "register_agent",
    "get_agent",
    "list_agents",
]
