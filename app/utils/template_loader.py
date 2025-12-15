"""
模板加载器 - 用于加载和渲染 Jinja2 模板
"""
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any, Optional


# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "prompts"


def get_template_env() -> Environment:
    """获取 Jinja2 环境"""
    if not TEMPLATES_DIR.exists():
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def load_template(template_name: str) -> str:
    """
    加载模板文件内容
    
    Args:
        template_name: 模板文件名（如 "rag_instructions.j2"）
    
    Returns:
        模板内容字符串
    """
    env = get_template_env()
    template = env.get_template(template_name)
    return template


def render_template(template_name: str, **kwargs) -> str:
    """
    渲染模板
    
    Args:
        template_name: 模板文件名
        **kwargs: 模板变量
    
    Returns:
        渲染后的字符串
    """
    template = load_template(template_name)
    return template.render(**kwargs)


def get_system_message_from_template(
    template_name: str = "rag_instructions.j2",
    **kwargs
) -> str:
    """
    从模板获取系统消息
    
    Args:
        template_name: 模板文件名
        **kwargs: 模板变量
    
    Returns:
        系统消息字符串
    """
    return render_template(template_name, **kwargs)
