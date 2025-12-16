# agent/registry.py
from typing import Callable, Dict

# 注册表
_AGENT_REGISTRY: Dict[str, Callable] = {}

def register_agent(name: str, factory: Callable):
    """注册一个 agent"""
    _AGENT_REGISTRY[name] = factory

def get_agent(name: str):
    """获取 agent 实例"""
    factory = _AGENT_REGISTRY.get(name)
    if not factory:
        raise ValueError(f"Agent '{name}' not found")
    return factory()

def list_agents():
    """列出所有可用 agent"""
    return list(_AGENT_REGISTRY.keys())
