"""
检索相关功能
"""
from langchain_community.vectorstores import PGVector
from langchain.schema import BaseRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI
from typing import Optional
from app.config import settings
from app.rag.vector_store import get_vector_store, get_embeddings


def get_retriever(
    vector_store: Optional[PGVector] = None,
    top_k: Optional[int] = None,
    use_compression: bool = False,
    llm: Optional[ChatOpenAI] = None
) -> BaseRetriever:
    """
    获取检索器
    
    Args:
        vector_store: 向量存储实例，如果不提供则使用默认的
        top_k: 返回的文档数量，默认使用配置中的值
        use_compression: 是否使用压缩检索器（使用 LLM 压缩检索结果）
        llm: LLM 实例，在使用压缩检索器时需要
    
    Returns:
        检索器实例
    """
    if vector_store is None:
        vector_store = get_vector_store()
    
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K
    
    # 基础检索器
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )
    
    # 如果需要压缩检索器
    if use_compression:
        if llm is None:
            llm = ChatOpenAI(
                model_name=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                openai_api_base=settings.OPENAI_API_BASE,
                temperature=0,
            )
        
        compressor = LLMChainExtractor.from_llm(llm)
        retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=retriever
        )
    
    return retriever
