"""
数据库工具函数
"""
import os
import psycopg2
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "rag"),
    "user": os.getenv("POSTGRES_USER", "rag"),
    "password": os.getenv("POSTGRES_PASSWORD", "rag"),
}


def get_db_connection():
    """获取数据库连接"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        raise ConnectionError(f"数据库连接失败: {str(e)}")


def get_document_chunk_embeddings(document_id: int) -> List[Dict[str, Any]]:
    """
    查询指定文档的所有 chunk 的 embedding
    
    Args:
        document_id: 文档 ID
        
    Returns:
        包含 chunk 信息的列表，每个元素包含:
        - id: chunk ID
        - chunk_index: chunk 索引
        - content: chunk 内容
        - embedding: embedding 向量（列表格式）
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 查询 document_chunk 的 embedding
            # 注意：PostgreSQL 的 vector 类型需要转换为数组
            cur.execute(
                """
                SELECT 
                    id,
                    chunk_index,
                    content,
                    embedding::text as embedding_text
                FROM public.document_chunk
                WHERE document_id = %s
                ORDER BY chunk_index ASC
                """,
                (document_id,)
            )
            
            results = []
            for row in cur.fetchall():
                chunk_id, chunk_index, content, embedding_text = row
                
                # 将 PostgreSQL vector 文本格式转换为列表
                # vector 格式: [0.1,0.2,0.3,...]
                embedding = None
                if embedding_text:
                    # 移除方括号并分割
                    embedding_str = embedding_text.strip('[]')
                    embedding = [float(x) for x in embedding_str.split(',')]
                
                results.append({
                    "id": chunk_id,
                    "chunk_index": chunk_index,
                    "content": content,
                    "embedding": embedding,
                    "embedding_dimension": len(embedding) if embedding else 0
                })
            
            return results
    finally:
        conn.close()


def get_document_info(document_id: int) -> Optional[Dict[str, Any]]:
    """
    获取文档基本信息
    
    Args:
        document_id: 文档 ID
        
    Returns:
        文档信息字典，如果不存在返回 None
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, source_url, title, content, content_hash, created_at
                FROM public.document
                WHERE id = %s
                """,
                (document_id,)
            )
            row = cur.fetchone()
            
            if not row:
                return None
            
            return {
                "id": row[0],
                "source_url": row[1],
                "title": row[2],
                "content": row[3],
                "content_hash": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            }
    finally:
        conn.close()


def search_similar_chunks(
    query_embedding: List[float],
    top_k: int = 5,
    similarity_threshold: float = 0.0
) -> List[Dict[str, Any]]:
    """
    使用向量相似度搜索相关的 chunks
    
    Args:
        query_embedding: 查询文本的 embedding 向量
        top_k: 返回最相似的 k 个结果
        similarity_threshold: 相似度阈值（0-1），低于此值的结果将被过滤
        
    Returns:
        包含相似 chunks 的列表，每个元素包含:
        - id: chunk ID
        - document_id: 文档 ID
        - chunk_index: chunk 索引
        - content: chunk 内容
        - similarity: 相似度分数（余弦相似度）
        - document_title: 文档标题
        - document_url: 文档 URL
    """
    if not query_embedding:
        return []
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 先检查数据库中是否有数据
            cur.execute("SELECT COUNT(*) FROM public.document_chunk WHERE embedding IS NOT NULL")
            total_chunks = cur.fetchone()[0]
            print(f"[调试] 数据库中总共有 {total_chunks} 个有 embedding 的 chunks")
            
            if total_chunks == 0:
                print("[警告] 数据库中没有包含 embedding 的 chunks，请先运行数据导入脚本")
                return []
            
            # 将 embedding 列表转换为 PostgreSQL vector 格式字符串
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            print(f"[调试] Query embedding 维度: {len(query_embedding)}")
            print(f"[调试] Embedding 字符串长度: {len(embedding_str)} (前100字符: {embedding_str[:100]}...)")
            
            # 先查询 top_k 个最相似的结果（不应用阈值过滤）
            try:
                # 使用子查询先计算相似度，避免 ORDER BY 可能的问题
                cur.execute(
                    """
                    WITH similarity_scores AS (
                        SELECT 
                            dc.id,
                            dc.document_id,
                            dc.chunk_index,
                            dc.content,
                            1 - (dc.embedding <=> %s::vector) as similarity,
                            d.title as document_title,
                            d.source_url as document_url
                        FROM public.document_chunk dc
                        JOIN public.document d ON dc.document_id = d.id
                        WHERE dc.embedding IS NOT NULL
                    )
                    SELECT 
                        id,
                        document_id,
                        chunk_index,
                        content,
                        similarity,
                        document_title,
                        document_url
                    FROM similarity_scores
                    WHERE similarity IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT %s
                    """,
                    (embedding_str, top_k * 2)  # 多查询一些，然后过滤
                )
                rows = cur.fetchall()
                print(f"[调试] SQL 查询返回 {len(rows)} 行结果")
            except Exception as e:
                print(f"[错误] SQL 查询执行失败: {e}")
                import traceback
                traceback.print_exc()
                return []
            
            all_candidates = []
            results = []
            for row in rows:
                chunk_id, doc_id, chunk_index, content, similarity, doc_title, doc_url = row
                similarity_value = float(similarity) if similarity else 0.0
                
                # 记录所有候选结果用于调试
                all_candidates.append({
                    "doc_id": doc_id,
                    "similarity": similarity_value,
                    "title": doc_title
                })
                
                # 应用相似度阈值过滤
                if similarity_value >= similarity_threshold:
                    results.append({
                        "id": chunk_id,
                        "document_id": doc_id,
                        "chunk_index": chunk_index,
                        "content": content,
                        "similarity": similarity_value,
                        "document_title": doc_title,
                        "document_url": doc_url
                    })
            
            # 打印所有候选结果的相似度（用于调试）
            if all_candidates:
                print(f"[调试] 查询到的前 {len(all_candidates)} 个候选文档相似度:")
                for i, cand in enumerate(all_candidates[:5], 1):
                    print(f"  [{i}] Doc ID: {cand['doc_id']}, 相似度: {cand['similarity']:.4f}, 标题: {cand['title']}")
            
            # 打印调试信息
            if results:
                print(f"[调试] 检索到 {len(results)} 个文档（阈值: {similarity_threshold}）")
                for i, r in enumerate(results[:3], 1):  # 只打印前3个
                    print(f"  [{i}] Doc ID: {r['document_id']}, 相似度: {r['similarity']:.4f}")
            else:
                print(f"[调试] 未找到满足阈值 {similarity_threshold} 的文档")
                # 查询最相似的一个用于调试
                if total_chunks > 0:
                    try:
                        cur.execute(
                            """
                            WITH similarity_scores AS (
                                SELECT 
                                    dc.id,
                                    dc.document_id,
                                    dc.chunk_index,
                                    dc.content,
                                    1 - (dc.embedding <=> %s::vector) as similarity,
                                    d.title as document_title,
                                    d.source_url as document_url
                                FROM public.document_chunk dc
                                JOIN public.document d ON dc.document_id = d.id
                                WHERE dc.embedding IS NOT NULL
                            )
                            SELECT 
                                id,
                                document_id,
                                chunk_index,
                                content,
                                similarity,
                                document_title,
                                document_url
                            FROM similarity_scores
                            WHERE similarity IS NOT NULL
                            ORDER BY similarity DESC
                            LIMIT 1
                            """,
                            (embedding_str,)
                        )
                        row = cur.fetchone()
                        if row:
                            chunk_id, doc_id, chunk_index, content, similarity, doc_title, doc_url = row
                            max_similarity = float(similarity) if similarity else 0.0
                            print(f"[调试] 最相似的文档相似度: {max_similarity:.4f} (低于阈值 {similarity_threshold})")
                            print(f"[调试] 最相似文档标题: {doc_title}")
                            # 安全处理内容预览，避免编码错误
                            try:
                                content_preview = content[:100] if content else ""
                                print(f"[调试] 最相似文档内容预览: {content_preview}...")
                            except Exception:
                                print(f"[调试] 最相似文档内容预览: [内容包含特殊字符，无法显示]")
                        else:
                            print("[调试] 查询最相似文档时返回空结果")
                    except Exception as e:
                        print(f"[调试] 查询最相似文档时出错: {e}")
            
            return results
    except Exception as e:
        print(f"[错误] 向量搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()
