"""
文本分割器 - 用于将文档分割成小块
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List


def create_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    separators: List[str] = None
) -> RecursiveCharacterTextSplitter:
    """
    创建文本分割器
    
    Args:
        chunk_size: 每个块的最大字符数
        chunk_overlap: 块之间的重叠字符数
        separators: 分割符列表，默认使用 RecursiveCharacterTextSplitter 的默认值
    
    Returns:
        RecursiveCharacterTextSplitter 实例
    """
    splitter_kwargs = {
        'chunk_size': chunk_size,
        'chunk_overlap': chunk_overlap,
        'length_function': len,
    }
    
    if separators:
        splitter_kwargs['separators'] = separators
    
    return RecursiveCharacterTextSplitter(**splitter_kwargs)


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
    """
    分割文本
    
    Args:
        text: 要分割的文本
        chunk_size: 每个块的最大字符数
        chunk_overlap: 块之间的重叠字符数
    
    Returns:
        分割后的文本块列表
    """
    splitter = create_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)


# 默认分割器实例
default_splitter = create_splitter(chunk_size=500, chunk_overlap=100)
