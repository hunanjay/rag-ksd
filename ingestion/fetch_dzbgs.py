import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import hashlib
import os
import sys
import psycopg2
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ingestion.splitter import split_text

load_dotenv()

# 要爬的列表
urls = [
    "https://www.jxstnu.edu.cn/info/1781/70441.htm"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Accept": "text/html,application/xhtml+xml"
}

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "rag"),
    "user": os.getenv("POSTGRES_USER", "rag"),
    "password": os.getenv("POSTGRES_PASSWORD", "rag"),
}

# Embedding 配置
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")


def get_db_connection():
    """获取数据库连接"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"\n❌ 数据库连接失败!")
        print(f"  配置信息:")
        print(f"    主机: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"    数据库: {DB_CONFIG['database']}")
        print(f"    用户: {DB_CONFIG['user']}")
        print(f"  错误详情: {str(e)}")
        print(f"\n💡 请检查:")
        print(f"  1. PostgreSQL 服务是否正在运行")
        print(f"  2. .env 文件中的数据库配置是否正确")
        print(f"  3. 数据库 '{DB_CONFIG['database']}' 是否存在")
        print(f"  4. 用户 '{DB_CONFIG['user']}' 是否有访问权限")
        print(f"  5. 防火墙是否允许连接到端口 {DB_CONFIG['port']}")
        raise
    except Exception as e:
        print(f"\n❌ 数据库连接时发生未知错误: {str(e)}")
        raise


def calculate_hash(text: str) -> str:
    """计算文本的 SHA256 哈希值"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def get_embeddings_model():
    """获取 embedding 模型，指定 1024 维度"""
    kwargs = {
        "model": EMBEDDING_MODEL,
        "openai_api_key": OPENAI_API_KEY,
        "dimensions": 1024,  # 指定生成 1024 维度的向量，匹配数据库 schema
    }
    if OPENAI_BASE_URL:
        kwargs["openai_api_base"] = OPENAI_BASE_URL
    return OpenAIEmbeddings(**kwargs)


def fetch(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = resp.apparent_encoding
        return resp.text
    except Exception as e:
        print(f"请求失败: {url} => {e}")
        return ""


def parse_content(html, base_url):
    soup = BeautifulSoup(html, "lxml")

    # 标题
    title = soup.find("title").get_text(strip=True) if soup.find("title") else ""

    # 尽量找正文区域
    main = soup.find("div", class_="news_content") or soup.find("div", id="content") or soup

    # 获取纯文本
    text = main.get_text("\n", strip=True)

    # 获取图片
    imgs = []
    for img in main.find_all("img"):
        src = img.get("src")
        if src:
            imgs.append(urljoin(base_url, src))

    return {
        "title": title,
        "text": text,
        "images": imgs
    }


def save_document_to_db(url: str, title: str, content: str, content_hash: str) -> int:
    """
    保存文档到数据库，返回 document_id
    如果 content_hash 已存在，返回现有文档的 ID
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 检查是否已存在相同 hash 的文档
            cur.execute(
                "SELECT id FROM public.document WHERE content_hash = %s",
                (content_hash,)
            )
            existing = cur.fetchone()
            
            if existing:
                doc_id = existing[0]
                print(f"  文档已存在 (hash 相同)，ID: {doc_id}")
                return doc_id
            
            # 插入新文档
            cur.execute(
                """
                INSERT INTO public.document (source_url, title, content, content_hash)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (url, title, content, content_hash)
            )
            doc_id = cur.fetchone()[0]
            conn.commit()
            print(f"  文档已保存，ID: {doc_id}")
            return doc_id
    finally:
        conn.close()


def save_chunks_to_db(document_id: int, chunks: list, embeddings_model):
    """
    保存 chunks 到数据库，并生成 embeddings
    """
    if not chunks:
        print("  没有 chunks 需要保存")
        return
    
    conn = get_db_connection()
    try:
        # 生成 embeddings
        print(f"  正在生成 {len(chunks)} 个 chunks 的 embeddings...")
        embeddings = embeddings_model.embed_documents(chunks)
        
        with conn.cursor() as cur:
            # 逐个插入 chunks（因为 vector 类型需要特殊处理）
            for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                # 将 embedding 列表转换为 PostgreSQL vector 格式字符串
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                cur.execute(
                    """
                    INSERT INTO public.document_chunk (document_id, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    (document_id, idx, chunk_text, embedding_str)
                )
            conn.commit()
            print(f"  {len(chunks)} 个 chunks 已保存并生成 embeddings")
    finally:
        conn.close()


def process_and_save(data: dict, embeddings_model):
    """
    处理单个文档：计算 hash、保存到数据库、划分 chunks、生成 embeddings
    """
    url = data["url"]
    title = data["title"]
    text = data["text"]
    
    if not text or not text.strip():
        print(f"跳过空内容: {url}")
        return
    
    # 计算 content_hash
    content_hash = calculate_hash(text)
    print(f"处理文档: {title}")
    print(f"  URL: {url}")
    print(f"  Hash: {content_hash[:16]}...")
    
    # 保存文档到数据库
    doc_id = save_document_to_db(url, title, text, content_hash)
    
    # 检查是否需要更新 chunks（如果文档已存在且 hash 相同，可能不需要重新生成）
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM public.document_chunk WHERE document_id = %s",
                (doc_id,)
            )
            chunk_count = cur.fetchone()[0]
            
            if chunk_count > 0:
                print(f"  文档已有 {chunk_count} 个 chunks，跳过重新生成")
                return
    finally:
        conn.close()
    
    # 划分 chunks
    print(f"  正在划分 chunks...")
    chunks = split_text(text, chunk_size=500, chunk_overlap=100)
    print(f"  划分为 {len(chunks)} 个 chunks")
    
    # 保存 chunks 并生成 embeddings
    save_chunks_to_db(doc_id, chunks, embeddings_model)


def spider():
    """爬取数据并保存到数据库"""
    results = []
    for url in urls:
        html = fetch(url)
        if not html:
            continue

        data = parse_content(html, url)
        data["url"] = url
        results.append(data)

        print(f"抓取成功: {url}")
        time.sleep(1)

    return results


if __name__ == "__main__":
    # 获取 embedding 模型
    print("初始化 embedding 模型...")
    embeddings_model = get_embeddings_model()
    
    # 爬取数据
    print("开始爬取数据...")
    data_list = spider()
    
    # 处理并保存每个文档
    print("\n开始保存数据到数据库...")
    for data in data_list:
        try:
            process_and_save(data, embeddings_model)
            print()
        except Exception as e:
            print(f"处理文档时出错: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("完成！")
