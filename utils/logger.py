"""
日志工具
"""
import logging
import sys
from app.config import settings


def setup_logger(name: str = "app", level: Optional[int] = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别，如果不提供则根据配置决定
    
    Returns:
        配置好的日志记录器
    """
    if level is None:
        level = logging.DEBUG if settings.VERBOSE else logging.INFO
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 创建控制台 handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger
