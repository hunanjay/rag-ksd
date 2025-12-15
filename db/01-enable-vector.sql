# enable vector extension
CREATE EXTENSION IF NOT EXISTSvector;
CREATE TABLE IF NOT EXISTS public.document (
    id BIGSERIAL PRIMARY KEY,
    source_url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.document_chunk (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT REFERENCES public.document(id) ON DELETE CASCADE,
    chunk_index INT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- 添加 embedding 列
ALTER TABLE public.document_chunk
ADD COLUMN embedding vector(1024);

-- 创建向量索引
CREATE INDEX IF NOT EXISTS idx_document_chunk_embedding
ON public.document_chunk
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
