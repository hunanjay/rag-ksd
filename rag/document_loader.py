"""
文档加载器
"""
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    CSVLoader,
    JSONLoader,
)
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List, Optional
from pathlib import Path


def load_documents(
    file_path: str,
    file_type: Optional[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Document]:
    """
    加载文档并分割
    
    Args:
        file_path: 文件路径或目录路径
        file_type: 文件类型（txt, pdf, csv, json），如果为 None 则自动推断
        chunk_size: 文本块大小
        chunk_overlap: 文本块重叠大小
    
    Returns:
        文档列表
    """
    path = Path(file_path)
    
    # 自动推断文件类型
    if file_type is None:
        if path.is_file():
            file_type = path.suffix.lower().lstrip(".")
        else:
            file_type = "txt"  # 目录默认按 txt 处理
    
    # 加载文档
    if path.is_file():
        loader = _get_file_loader(str(path), file_type)
        documents = loader.load()
    else:
        # 目录加载
        glob_pattern = f"*.{file_type}" if file_type != "txt" else "*.txt"
        loader = DirectoryLoader(
            str(path),
            glob=glob_pattern,
            loader_cls=_get_loader_class(file_type),
        )
        documents = loader.load()
    
    # 分割文档
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    splits = text_splitter.split_documents(documents)
    
    return splits


def _get_file_loader(file_path: str, file_type: str):
    """根据文件类型获取对应的加载器"""
    loader_map = {
        "txt": TextLoader,
        "pdf": PyPDFLoader,
        "csv": CSVLoader,
        "json": JSONLoader,
    }
    
    loader_class = loader_map.get(file_type.lower())
    if loader_class is None:
        raise ValueError(f"不支持的文件类型: {file_type}")
    
    if file_type == "json":
        return loader_class(file_path, jq_schema=".")
    return loader_class(file_path)


def _get_loader_class(file_type: str):
    """获取目录加载器使用的加载器类"""
    loader_map = {
        "txt": TextLoader,
        "pdf": PyPDFLoader,
        "csv": CSVLoader,
        "json": lambda path: JSONLoader(path, jq_schema="."),
    }
    
    loader_class = loader_map.get(file_type.lower())
    if loader_class is None:
        raise ValueError(f"不支持的文件类型: {file_type}")
    
    return loader_class
