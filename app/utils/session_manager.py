"""
Session 管理器 - 使用 PostgreSQL 存储会话
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库配置（复用现有的配置）
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "rag"),
    "user": os.getenv("POSTGRES_USER", "rag"),
    "password": os.getenv("POSTGRES_PASSWORD", "rag"),
}

# Session 过期时间（默认 30 分钟）
SESSION_EXPIRE_MINUTES = int(os.getenv("SESSION_EXPIRE_MINUTES", "30"))


def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(**DB_CONFIG)


def create_session(user_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> str:
    """
    创建新的 session
    
    Args:
        user_id: 用户ID
        ip_address: 客户端IP地址
        user_agent: 用户代理字符串
    
    Returns:
        session_id: 会话ID
    """
    session_id = secrets.token_urlsafe(32)  # 生成安全的随机字符串
    expires_at = datetime.now() + timedelta(minutes=SESSION_EXPIRE_MINUTES)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO public.sessions (session_id, user_id, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_id, user_id, expires_at, ip_address, user_agent))
            conn.commit()
            return session_id
    finally:
        conn.close()


def get_session(session_id: str) -> Optional[Dict]:
    """
    获取 session 信息
    
    Args:
        session_id: 会话ID
    
    Returns:
        session 信息字典，如果不存在或已过期则返回 None
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT s.*, u.username, u.is_admin, u.is_active
                FROM public.sessions s
                JOIN public.users u ON s.user_id = u.id
                WHERE s.session_id = %s AND s.expires_at > now()
            """, (session_id,))
            result = cur.fetchone()
            
            if result:
                # 更新最后访问时间
                cur.execute("""
                    UPDATE public.sessions
                    SET last_accessed_at = now()
                    WHERE session_id = %s
                """, (session_id,))
                conn.commit()
                return dict(result)
            return None
    finally:
        conn.close()


def delete_session(session_id: str) -> bool:
    """
    删除 session
    
    Args:
        session_id: 会话ID
    
    Returns:
        是否成功删除
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM public.sessions WHERE session_id = %s", (session_id,))
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()


def delete_user_sessions(user_id: int) -> int:
    """
    删除用户的所有 session（用于登出所有设备）
    
    Args:
        user_id: 用户ID
    
    Returns:
        删除的 session 数量
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM public.sessions WHERE user_id = %s", (user_id,))
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()


def cleanup_expired_sessions():
    """
    清理过期的 session（可以定期运行，比如每天）
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM public.sessions WHERE expires_at < now()")
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()
