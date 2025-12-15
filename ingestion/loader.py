"""
文档加载器 - 统一的文档加载接口
"""
from pathlib import Path
from typing import List, Optional
from langchain.schema import Document

from .parser import parse_file
from .splitter import split_text, create_splitter


def load_document(
    file_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    split: bool = True
) -> List[Document]:
    """
    加载文档并可选择性地分割
    
    Args:
        file_path: 文件路径
        chunk_size: 分割时的块大小
        chunk_overlap: 分割时的重叠大小
        split: 是否分割文档
    
    Returns:
        文档列表（Document 对象列表）
    """
    # 解析文件获取文本内容
    text = parse_file(file_path)
    
    # 获取文件元数据
    path = Path(file_path)
    metadata = {
        "source": str(path.absolute()),
        "file_name": path.name,
        "file_type": path.suffix,
    }
    
    if split:
        # 分割文本
        chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        # 创建 Document 对象列表
        documents = []
        for idx, chunk in enumerate(chunks):
            doc_metadata = {**metadata, "chunk_index": idx}
            documents.append(Document(page_content=chunk, metadata=doc_metadata))
        
        return documents
    else:
        # 不分割，返回单个文档
        return [Document(page_content=text, metadata=metadata)]


def load_documents_from_directory(
    directory: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    split: bool = True,
    recursive: bool = True
) -> List[Document]:
    """
    从目录加载多个文档
    
    Args:
        directory: 目录路径
        chunk_size: 分割时的块大小
        chunk_overlap: 分割时的重叠大小
        split: 是否分割文档
        recursive: 是否递归搜索子目录
    
    Returns:
        文档列表
    """
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        raise ValueError(f"目录不存在或不是目录: {directory}")
    
    all_documents = []
    
    # 支持的扩展名
    from .parser import SUPPORTED_EXTENSIONS
    extensions = list(SUPPORTED_EXTENSIONS.keys())
    
    # 查找所有支持的文件
    pattern = "**/*" if recursive else "*"
    for file_path in dir_path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            try:
                docs = load_document(
                    str(file_path),
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    split=split
                )
                all_documents.extend(docs)
            except Exception as e:
                print(f"警告: 加载文件失败 {file_path}: {e}")
                continue
    
    return all_documents
