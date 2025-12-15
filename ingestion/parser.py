"""
文件解析器 - 支持多种文件格式的解析
"""
from pathlib import Path
from typing import Optional, List
import mimetypes

# LangChain 文档加载器
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    UnstructuredWordDocumentLoader,
)


SUPPORTED_EXTENSIONS = {
    '.txt': TextLoader,
    '.md': UnstructuredMarkdownLoader,
    '.pdf': PyPDFLoader,
    '.csv': CSVLoader,
    '.json': JSONLoader,
    '.html': UnstructuredHTMLLoader,
    '.htm': UnstructuredHTMLLoader,
    '.docx': UnstructuredWordDocumentLoader,
    '.doc': UnstructuredWordDocumentLoader,
}


def parse_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    解析文件并返回文本内容
    
    Args:
        file_path: 文件路径
        encoding: 文本文件的编码（仅对文本文件有效）
    
    Returns:
        文件文本内容
    
    Raises:
        ValueError: 不支持的文件类型
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_ext = path.suffix.lower()
    
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {file_ext}")
    
    loader_class = SUPPORTED_EXTENSIONS[file_ext]
    
    # 特殊处理 JSON 文件
    if file_ext == '.json':
        loader = loader_class(str(path), jq_schema=".")
    else:
        loader = loader_class(str(path))
    
    # 加载文档
    documents = loader.load()
    
    # 合并所有文档的文本内容
    texts = [doc.page_content for doc in documents]
    return "\n\n".join(texts)


def parse_file_simple(file_path: str, encoding: str = "utf-8") -> str:
    """
    简单解析文本文件（仅支持纯文本文件）
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        文件文本内容
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(path, 'r', encoding=encoding) as f:
        return f.read()


def get_supported_extensions() -> List[str]:
    """
    获取支持的文件扩展名列表
    
    Returns:
        支持的文件扩展名列表
    """
    return list(SUPPORTED_EXTENSIONS.keys())


def is_supported(file_path: str) -> bool:
    """
    检查文件类型是否支持
    
    Args:
        file_path: 文件路径
    
    Returns:
        是否支持该文件类型
    """
    path = Path(file_path)
    return path.suffix.lower() in SUPPORTED_EXTENSIONS
