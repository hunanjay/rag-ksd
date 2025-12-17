"""
Agent 基类 - 提供默认的流式支持
"""
from typing import Any, Dict, AsyncIterator
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Agent 基类，提供默认的流式支持。
    
    如果子类没有实现 astream，会自动使用 invoke 方法并模拟流式输出。
    如果子类有 llm 属性，可以直接使用 llm.astream 进行流式输出。
    """
    
    @abstractmethod
    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行一次对话（非流式）。
        
        Args:
            inputs: 输入字典，包含 "input" 和可选的 "chat_history"
        
        Returns:
            包含 "output" 和 "intermediate_steps" 的字典
        """
        pass
    
    async def astream(self, inputs: Dict[str, Any]) -> AsyncIterator[str]:
        """
        流式执行对话（默认实现）。
        
        默认实现会调用 invoke 方法，然后模拟流式输出。
        子类可以覆盖此方法以实现真正的流式输出（如使用 llm.astream）。
        
        Args:
            inputs: 输入字典，包含 "input" 和可选的 "chat_history"
        
        Yields:
            文本内容字符串
        """
        # 默认：调用 invoke 然后模拟流式输出
        result = self.invoke(inputs)
        output = result.get("output", "")
        
        # 模拟流式输出（逐字符发送，可以改为逐词或逐句）
        for char in output:
            yield char
