"""
向量存储相关功能
"""
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from typing import Optional
from app.config import settings


def get_embeddings() -> OpenAIEmbeddings:
    """获取嵌入模型"""
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        openai_api_base=settings.OPENAI_API_BASE,
    )


def get_vector_store(
    collection_name: Optional[str] = None,
    embeddings: Optional[OpenAIEmbeddings] = None
) -> PGVector:
    """
    获取向量存储实例
    
    Args:
        collection_name: 集合名称，默认为配置中的向量表名
        embeddings: 嵌入模型，如果不提供则使用默认的
    
    Returns:
        PGVector 向量存储实例
    """
    if embeddings is None:
        embeddings = get_embeddings()
    
    if collection_name is None:
        collection_name = settings.VECTOR_TABLE_NAME
    
    # 构建连接字符串
    connection_string = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    
    return PGVector(
        connection_string=connection_string,
        embedding_function=embeddings,
        collection_name=collection_name,
    )
