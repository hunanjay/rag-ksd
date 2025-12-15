"""
RAG Chain 相关功能
"""
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.schema import BaseRetriever
from langchain.prompts import PromptTemplate
from typing import Optional
from app.config import settings
from app.rag.retrieval import get_retriever
from app.rag.vector_store import get_vector_store


def create_rag_chain(
    retriever: Optional[BaseRetriever] = None,
    llm: Optional[ChatOpenAI] = None,
    prompt_template: Optional[PromptTemplate] = None,
    return_source_documents: bool = True
) -> RetrievalQA:
    """
    创建 RAG Chain
    
    Args:
        retriever: 检索器，如果不提供则使用默认的
        llm: LLM 实例，如果不提供则使用默认的
        prompt_template: 提示词模板，如果不提供则使用默认的
        return_source_documents: 是否返回源文档
    
    Returns:
        RetrievalQA Chain 实例
    """
    if retriever is None:
        vector_store = get_vector_store()
        retriever = get_retriever(vector_store=vector_store)
    
    if llm is None:
        llm = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            streaming=True,
            temperature=0,
        )
    
    if prompt_template is None:
        prompt_template = _get_default_prompt_template()
    
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=return_source_documents,
        chain_type_kwargs={"prompt": prompt_template},
    )
    
    return chain


def _get_default_prompt_template() -> PromptTemplate:
    """获取默认的提示词模板"""
    template = """使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要编造答案。

上下文：
{context}

问题：{question}

回答："""
    
    return PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
