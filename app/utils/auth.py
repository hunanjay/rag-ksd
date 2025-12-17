"""
用户认证工具 - 明文密码存储和验证
"""
import os
from typing import Optional, Dict
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "rag"),
    "user": os.getenv("POSTGRES_USER", "rag"),
    "password": os.getenv("POSTGRES_PASSWORD", "rag"),
}


def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(**DB_CONFIG)


def verify_password(password: str, stored_password: str) -> bool:
    """
    验证密码（明文比较）
    
    Args:
        password: 用户输入的明文密码
        stored_password: 数据库中存储的明文密码
    
    Returns:
        是否匹配
    """
    return password == stored_password


def get_user_by_username(username: str) -> Optional[Dict]:
    """
    根据用户名获取用户信息
    
    Args:
        username: 用户名
    
    Returns:
        用户信息字典，如果不存在则返回 None
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, username, email, password, is_active, is_admin, created_at
                FROM public.users
                WHERE username = %s
            """, (username,))
            result = cur.fetchone()
            return dict(result) if result else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    根据用户ID获取用户信息
    
    Args:
        user_id: 用户ID
    
    Returns:
        用户信息字典，如果不存在则返回 None
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, username, email, password, is_active, is_admin, created_at
                FROM public.users
                WHERE id = %s
            """, (user_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    finally:
        conn.close()


def create_user(username: str, password: str, email: Optional[str] = None, is_admin: bool = False) -> Optional[int]:
    """
    创建新用户（明文密码存储）
    
    Args:
        username: 用户名
        password: 明文密码
        email: 邮箱（可选）
        is_admin: 是否为管理员
    
    Returns:
        用户ID，如果创建失败则返回 None
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO public.users (username, email, password, is_admin)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (username, email, password, is_admin))
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
    except psycopg2.IntegrityError:
        # 用户名或邮箱已存在
        conn.rollback()
        return None
    finally:
        conn.close()
