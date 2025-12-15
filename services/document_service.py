"""
文档服务 - 处理文档的上传、存储和索引
"""
from typing import List, Optional
from langchain.schema import Document
from app.rag.document_loader import load_documents
from app.rag.vector_store import get_vector_store


class DocumentService:
    """文档服务类"""
    
    def __init__(self, collection_name: Optional[str] = None):
        """
        初始化文档服务
        
        Args:
            collection_name: 向量集合名称
        """
        self.vector_store = get_vector_store(collection_name=collection_name)
        self.collection_name = collection_name
    
    def add_documents(
        self,
        file_path: str,
        file_type: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        metadata: Optional[dict] = None
    ) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            file_path: 文件路径或目录路径
            file_type: 文件类型
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠大小
            metadata: 额外的元数据
        
        Returns:
            文档 ID 列表
        """
        # 加载并分割文档
        documents = load_documents(
            file_path=file_path,
            file_type=file_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 添加元数据
        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)
        
        # 添加到向量存储
        ids = self.vector_store.add_documents(documents)
        
        return ids
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None
    ) -> List[str]:
        """
        直接添加文本到向量存储
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表
        
        Returns:
            文档 ID 列表
        """
        ids = self.vector_store.add_texts(texts, metadatas=metadatas)
        return ids
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None
    ) -> List[Document]:
        """
        搜索相似文档
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            filter: 过滤条件
        
        Returns:
            相似的文档列表
        """
        return self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter
        )
    
    def delete(self, ids: Optional[List[str]] = None, filter: Optional[dict] = None):
        """
        删除文档
        
        Args:
            ids: 要删除的文档 ID 列表
            filter: 过滤条件
        """
        self.vector_store.delete(ids=ids, filter=filter)
