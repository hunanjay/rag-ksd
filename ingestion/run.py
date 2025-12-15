"""
文档摄取主程序 - 示例使用
"""
from pathlib import Path
from typing import Optional
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.loader import load_document, load_documents_from_directory
from ingestion.embedder import generate_embedding, generate_embeddings_batch
from ingestion.fetch import fetch_page


def main():
    """主函数示例"""
    print("文档摄取模块示例")
    print("=" * 50)
    
    # 示例 1: 加载单个文档
    print("\n1. 加载单个文档:")
    try:
        # 这里需要替换为实际的文件路径
        # docs = load_document("path/to/your/file.txt", chunk_size=500, chunk_overlap=100)
        # print(f"加载了 {len(docs)} 个文档块")
        print("（需要提供实际文件路径）")
    except Exception as e:
        print(f"错误: {e}")
    
    # 示例 2: 生成嵌入
    print("\n2. 生成嵌入:")
    try:
        sample_text = "这是一个测试文本"
        embedding = generate_embedding(sample_text)
        print(f"嵌入向量长度: {len(embedding)}")
        print(f"前5个维度: {embedding[:5]}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 示例 3: 批量生成嵌入
    print("\n3. 批量生成嵌入:")
    try:
        texts = ["文本1", "文本2", "文本3"]
        embeddings = generate_embeddings_batch(texts)
        print(f"生成了 {len(embeddings)} 个嵌入向量")
        print(f"每个向量的长度: {len(embeddings[0]) if embeddings else 0}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 示例 4: 获取网页内容
    print("\n4. 获取网页内容:")
    try:
        # url = "https://example.com"
        # title, content = fetch_page(url)
        # print(f"标题: {title}")
        # print(f"内容长度: {len(content)}")
        print("（需要提供实际 URL）")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
