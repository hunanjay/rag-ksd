"""
网页内容获取模块 - 支持从 URL 获取数据
"""
import requests
from bs4 import BeautifulSoup
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import chardet
import argparse
import sys
import re


def fetch_page(
    url: str, 
    timeout: int = 10, 
    encoding: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    **kwargs
) -> Tuple[str, str]:
    """
    获取网页内容并提取标题和正文
    
    Args:
        url: 网页 URL（必需）
        timeout: 请求超时时间（秒），默认 10
        encoding: 响应编码，如果为 None 则自动检测
        headers: 自定义请求头字典
        **kwargs: 其他 requests.get() 支持的参数（如 cookies, auth 等）
    
    Returns:
        (title, text) 元组，包含标题和正文内容
    
    Raises:
        requests.RequestException: 请求失败时抛出
        Exception: 其他错误
    
    Examples:
        >>> title, text = fetch_page("https://example.com")
        >>> title, text = fetch_page("https://example.com", timeout=30, encoding="gbk")
        >>> title, text = fetch_page("https://api.example.com/data", headers={"Authorization": "Bearer token"})
    """
    try:
        # 准备请求参数
        request_kwargs = {"timeout": timeout, **kwargs}
        if headers:
            request_kwargs["headers"] = headers
        
        resp = requests.get(url, **request_kwargs)
        resp.raise_for_status()
        
        # 自动检测编码（如果未指定）
        if encoding is None:
            # 优先从 HTML meta 标签获取编码
            soup_temp = BeautifulSoup(resp.content[:5000], "html.parser")
            meta_charset = soup_temp.find('meta', {'charset': True})
            if meta_charset:
                encoding = meta_charset.get('charset', '').lower()
            if not encoding:
                meta_content = soup_temp.find('meta', attrs={'http-equiv': re.compile('content-type', re.I)})
                if meta_content and meta_content.get('content'):
                    import re
                    charset_match = re.search(r'charset=([^;]+)', meta_content['content'], re.I)
                    if charset_match:
                        encoding = charset_match.group(1).strip().lower()
            
            # 如果 HTML 中没有找到，使用 chardet 检测
            if not encoding:
                detected = chardet.detect(resp.content[:10000])
                detected_encoding = detected.get('encoding') if detected else None
                if detected_encoding and detected.get('confidence', 0) > 0.7:
                    encoding = detected_encoding.lower()
            
            # 标准化编码名称
            if encoding:
                encoding = encoding.lower().strip()
                if encoding in ['utf-8-sig', 'utf8-sig']:
                    encoding = 'utf-8-sig'
                elif encoding in ['utf-8', 'utf8']:
                    encoding = 'utf-8'
                elif encoding in ['gb2312', 'gbk', 'gb18030']:
                    encoding = 'gb18030'
                elif encoding == 'ascii':
                    encoding = 'utf-8'
            else:
                encoding = 'utf-8'
        
        # 解码内容
        try:
            html_content = resp.content.decode(encoding, errors='replace')
        except (UnicodeDecodeError, LookupError) as e:
            # 如果指定的编码失败，尝试其他编码
            for fallback_encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb18030', 'gb2312', 'latin-1']:
                try:
                    html_content = resp.content.decode(fallback_encoding, errors='replace')
                    encoding = fallback_encoding
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                html_content = resp.content.decode('utf-8', errors='replace')
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 提取标题
        title_tag = soup.find('title')
        title = title_tag.text.strip() if title_tag else url  # 如果没有标题，使用 URL
        
        # 尝试多种方式提取正文内容
        text = _extract_content(soup, url)
        
        return title, text
    
    except requests.RequestException as e:
        raise Exception(f"获取网页内容失败: {str(e)}")
    except Exception as e:
        raise Exception(f"处理网页内容时出错: {str(e)}")


def _extract_content(soup: BeautifulSoup, url: str = None) -> str:
    """
    从 HTML 中提取正文内容
    
    Args:
        soup: BeautifulSoup 对象
        url: 可选，用于相对链接转换
    
    Returns:
        提取的文本内容
    """
    # 尝试多种常见的内容选择器
    content_selectors = [
        ".v_news_content",  # 特定的内容类
        "article",
        "main",
        ".content",
        "#content",
        ".post-content",
        ".entry-content",
    ]
    
    for selector in content_selectors:
        content_div = soup.select_one(selector)
        if content_div:
            # 移除脚本和样式标签
            for script in content_div(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            return content_div.get_text("\n", strip=True)
    
    # 如果没有找到特定的内容区域，尝试提取 body 内容
    body = soup.find('body')
    if body:
        for script in body(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        return body.get_text("\n", strip=True)
    
    # 最后尝试提取整个文档
    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
        script.decompose()
    return soup.get_text("\n", strip=True)


def fetch_text_only(
    url: str, 
    timeout: int = 10,
    encoding: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    **kwargs
) -> str:
    """
    只获取文本内容（不返回标题）
    
    Args:
        url: 网页 URL（必需）
        timeout: 请求超时时间，默认 10
        encoding: 响应编码，如果为 None 则自动检测
        headers: 自定义请求头字典
        **kwargs: 其他 requests.get() 支持的参数
    
    Returns:
        文本内容
    
    Examples:
        >>> text = fetch_text_only("https://example.com")
        >>> text = fetch_text_only("https://api.example.com/data", headers={"Authorization": "Bearer token"})
    """
    _, text = fetch_page(url, timeout=timeout, encoding=encoding, headers=headers, **kwargs)
    return text


def fetch_url_as_text(
    url: str,
    timeout: int = 10,
    encoding: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    **kwargs
) -> str:
    """
    从 URL 获取文本内容（fetch_text_only 的别名，更直观）
    
    Args:
        url: 网页或文件 URL（必需）
        timeout: 请求超时时间，默认 10
        encoding: 响应编码，如果为 None 则自动检测
        headers: 自定义请求头字典
        **kwargs: 其他 requests.get() 支持的参数
    
    Returns:
        文本内容
    
    Examples:
        >>> text = fetch_url_as_text("https://example.com/article")
        >>> text = fetch_url_as_text("https://api.example.com/json", headers={"Accept": "application/json"})
    """
    return fetch_text_only(url, timeout=timeout, encoding=encoding, headers=headers, **kwargs)


def main():
    parser = argparse.ArgumentParser(description="从 URL 获取网页内容")
    parser.add_argument("url", help="网页 URL")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="超时时间（秒）")
    parser.add_argument("-e", "--encoding", type=str, default=None, help="编码，默认自动检测")
    parser.add_argument("-o", "--output", type=str, default=None, help="输出文件，默认 stdout")
    parser.add_argument("--title-only", action="store_true", help="仅输出标题")
    parser.add_argument("--text-only", action="store_true", help="仅输出文本")
    
    args = parser.parse_args()
    
    try:
        if args.title_only:
            title, _ = fetch_page(args.url, timeout=args.timeout, encoding=args.encoding)
            content = title
        elif args.text_only:
            content = fetch_text_only(args.url, timeout=args.timeout, encoding=args.encoding)
        else:
            title, text = fetch_page(args.url, timeout=args.timeout, encoding=args.encoding)
            content = f"{title}\n\n{text}"
        
        if args.output:
            with open(args.output, "w", encoding="utf-8", errors='replace') as f:
                f.write(content)
            print(f"已保存: {args.output}")
        else:
            try:
                print(content)
            except UnicodeEncodeError:
                print(content.encode('utf-8', errors='replace').decode('utf-8'))
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
