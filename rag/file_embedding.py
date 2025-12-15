"""
OpenAI Embedding 辅助模块
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from openai import OpenAI


DEFAULT_MODEL = "text-embedding-3-large"
DEFAULT_DIMENSION = 1024


def _get_openai_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> OpenAI:
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("缺少 OPENAI_API_KEY")

    base = base_url or os.getenv("OPENAI_BASE_URL")
    return OpenAI(api_key=key, base_url=base) if base else OpenAI(api_key=key)


def _read_file_text(file_path: str, max_chars: int) -> str:
    from tools.moodle_mcp.core.file_parser import parse_file_for_llm

    content = parse_file_for_llm(Path(file_path), max_chars=max_chars)
    if not content or not content.strip():
        raise ValueError("文件内容为空，无法生成 embedding")
    return content


def generate_file_embedding(
    file_path: str,
    openai_api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    dimension: int = DEFAULT_DIMENSION,
    max_chars: int = 8000,
) -> List[float]:
    """
    读取文件并生成 OpenAI embedding。
    """
    text = _read_file_text(file_path, max_chars)
    client = _get_openai_client(openai_api_key)
    kwargs: Dict[str, Any] = {
        "model": model,
        "input": text,
    }
    if dimension:
        kwargs["dimensions"] = dimension

    resp = client.embeddings.create(**kwargs)
    return resp.data[0].embedding


def save_embedding_to_db(file_id: int, embedding: List[float]) -> bool:
    from db.session import SessionLocal
    from db.tables.moodle_files import MoodleFile

    with SessionLocal() as session:
        record = session.query(MoodleFile).filter(MoodleFile.id == file_id).first()
        if not record:
            raise ValueError(f"未找到文件 ID: {file_id}")
        record.vector = embedding
        session.commit()
        return True


def generate_and_save_embedding(
    file_path: str,
    file_id: int,
    openai_api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    dimension: int = DEFAULT_DIMENSION,
    max_chars: int = 8000,
    skip_if_exists: bool = True,
) -> Dict[str, Any]:
    from db.session import SessionLocal
    from db.tables.moodle_files import MoodleFile

    if skip_if_exists:
        with SessionLocal() as session:
            record = session.query(MoodleFile).filter(MoodleFile.id == file_id).first()
            if record and record.vector is not None:
                return {"success": True, "file_id": file_id, "skipped": True}

    embedding = generate_file_embedding(
        file_path=file_path,
        openai_api_key=openai_api_key,
        model=model,
        dimension=dimension,
        max_chars=max_chars,
    )

    save_embedding_to_db(file_id, embedding)
    return {
        "success": True,
        "file_id": file_id,
        "embedding_length": len(embedding),
        "skipped": False,
    }


if __name__ == "__main__":
    sample_text = "今天是一个美好的一天，我在学习如何使用 embedding API。"
    client = _get_openai_client()
    resp = client.embeddings.create(model=DEFAULT_MODEL, input=sample_text, dimensions=DEFAULT_DIMENSION)
    vector = resp.data[0].embedding
    print("Embedding 长度:", len(vector))
    print("前 10 维:", vector[:10])
