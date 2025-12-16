"""
RAG Tools - 将数据库工具函数转换为 LangChain Tools
"""
from langchain.tools import tool
from langchain_openai import OpenAIEmbeddings
from typing import List
import os
from dotenv import load_dotenv
from app.utils.db_tools import search_similar_chunks, get_document_info

load_dotenv()

# 初始化 embedding 模型（用于将查询文本转换为向量）
_embeddings_model = None

def get_embeddings_model():
    """获取或创建 embedding 模型实例"""
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_BASE_URL"),
            dimensions=1024  # 匹配数据库中的向量维度
        )
    return _embeddings_model


@tool
def rag_search(
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.3
) -> str:
    """
    使用向量相似度搜索从知识库中检索相关文档内容。
    
    Args:
        query: 用户的问题或查询文本
        top_k: 返回最相似的文档数量，默认为 5
        similarity_threshold: 相似度阈值（0-1），低于此值的结果将被过滤，默认为 0.3
    
    Returns:
        返回检索到的文档内容，格式为：
        [文档1] 标题: xxx
        内容: xxx
        相似度: 0.xxx
        
        [文档2] ...
        
        如果没有找到相关文档，返回 "未找到相关文档"。
    """
    try:
        # 将查询文本转换为 embedding
        embeddings_model = get_embeddings_model()
        query_embedding = embeddings_model.embed_query(query)
        
        # 搜索相似的 chunks
        similar_chunks = search_similar_chunks(
            query_embedding=query_embedding,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        if not similar_chunks:
            return "未找到相关文档"
        
        # 格式化返回结果
        results = []
        for i, chunk in enumerate(similar_chunks, 1):
            result = f"[文档 {i}]\n"
            result += f"标题: {chunk.get('document_title', '未知')}\n"
            result += f"内容: {chunk.get('content', '')}\n"
            result += f"相似度: {chunk.get('similarity', 0.0):.4f}\n"
            if chunk.get('document_url'):
                result += f"来源: {chunk.get('document_url')}\n"
            results.append(result)
        
        return "\n\n".join(results)
    
    except Exception as e:
        return f"检索过程中发生错误: {str(e)}"


@tool
def get_document_details(document_id: int) -> str:
    """
    根据文档 ID 获取文档的详细信息。
    
    Args:
        document_id: 文档的唯一标识符（整数）
    
    Returns:
        返回文档的详细信息，包括：
        - 文档 ID
        - 标题
        - 内容
        - 来源 URL
        - 创建时间
        
        如果文档不存在，返回 "文档不存在"。
    """
    try:
        doc_info = get_document_info(document_id)
        
        if not doc_info:
            return f"文档 ID {document_id} 不存在"
        
        result = f"文档 ID: {doc_info['id']}\n"
        result += f"标题: {doc_info.get('title', '未知')}\n"
        result += f"来源: {doc_info.get('source_url', '未知')}\n"
        if doc_info.get('created_at'):
            result += f"创建时间: {doc_info['created_at']}\n"
        result += f"\n内容:\n{doc_info.get('content', '无内容')}"
        
        return result
    
    except Exception as e:
        return f"获取文档信息时发生错误: {str(e)}"


def get_rag_tools() -> List:
    """
    获取所有 RAG 相关的工具列表
    
    Returns:
        LangChain Tool 对象列表
    """
    return [rag_search, get_document_details]
