"""
文档摄取模块 - 用于加载、解析、分割和嵌入文档
"""
__all__ = [
    "split_text",
    "create_splitter",
    "default_splitter",
    "fetch_page",
    "fetch_text_only",
    "fetch_url_as_text",
    "parse_file",
    "parse_file_simple",
    "get_supported_extensions",
    "is_supported",
    "generate_embedding",
    "generate_embeddings_batch",
    "get_openai_client",
    "load_document",
    "load_documents_from_directory",
]

# 延迟导入，避免直接运行 fetch.py 时导入依赖 langchain 的模块
def __getattr__(name):
    if name in __all__:
        if name in ["fetch_page", "fetch_text_only", "fetch_url_as_text"]:
            from .fetch import fetch_page, fetch_text_only, fetch_url_as_text
            return {"fetch_page": fetch_page, "fetch_text_only": fetch_text_only, "fetch_url_as_text": fetch_url_as_text}[name]
        elif name in ["split_text", "create_splitter", "default_splitter"]:
            from .splitter import split_text, create_splitter, default_splitter
            return {"split_text": split_text, "create_splitter": create_splitter, "default_splitter": default_splitter}[name]
        elif name in ["parse_file", "parse_file_simple", "get_supported_extensions", "is_supported"]:
            from .parser import parse_file, parse_file_simple, get_supported_extensions, is_supported
            return {"parse_file": parse_file, "parse_file_simple": parse_file_simple, "get_supported_extensions": get_supported_extensions, "is_supported": is_supported}[name]
        elif name in ["generate_embedding", "generate_embeddings_batch", "get_openai_client"]:
            from .embedder import generate_embedding, generate_embeddings_batch, get_openai_client
            return {"generate_embedding": generate_embedding, "generate_embeddings_batch": generate_embeddings_batch, "get_openai_client": get_openai_client}[name]
        elif name in ["load_document", "load_documents_from_directory"]:
            from .loader import load_document, load_documents_from_directory
            return {"load_document": load_document, "load_documents_from_directory": load_documents_from_directory}[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
