"""
页面内容获取模块
从 URL 获取 HTML 内容，支持 requests（优先）和 Selenium（备选）
"""
import logging
import sys
from typing import Dict, Any

import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# 默认请求头，模拟浏览器
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def _extract_title_from_html(html: str, url: str) -> str:
    """从 HTML 中提取页面标题"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        # 优先从 <title> 提取
        title_tag = soup.find("title")
        if title_tag and title_tag.get_text(strip=True):
            return title_tag.get_text(strip=True)
        # 备选：从第一个 h1 提取
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)
        # 备选：从 og:title 提取
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
    except Exception as e:
        logger.warning(f"提取标题失败: {e}")
    return ""


def fetch_html_from_url(
    url: str,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    从指定 URL 获取 HTML 内容

    使用 requests 获取页面（支持大多数静态/服务端渲染页面）。
    适用于文章、博客、技术文档等。若页面为纯 JS 渲染，可能需配合 extract_links_from_url 等工具。

    参数:
        url: 页面 URL（如文章链接、GitHub 仓库等）
        timeout: 请求超时秒数

    返回:
        {
            "success": bool,
            "html": str,           # 完整 HTML 源码
            "title": str,          # 页面标题（从 <title> 或 h1 提取）
            "url": str,            # 实际请求的 URL（可能经过重定向）
            "status_code": int,    # HTTP 状态码
            "error": str           # 错误信息（失败时）
        }
    """
    if not url or not url.strip():
        return {
            "success": False,
            "html": "",
            "title": "",
            "url": url or "",
            "error": "URL 不能为空",
        }

    url = url.strip()

    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        html = response.text
        title = _extract_title_from_html(html, url)

        logger.info(f"从 {url} 获取 HTML 成功，长度 {len(html)} 字符")

        return {
            "success": True,
            "html": html,
            "title": title,
            "url": response.url,
            "status_code": response.status_code,
            "error": None,
        }
    except requests.exceptions.Timeout:
        logger.warning(f"请求超时: {url}")
        return {
            "success": False,
            "html": "",
            "title": "",
            "url": url,
            "error": f"请求超时（{timeout}秒）",
        }
    except requests.exceptions.RequestException as e:
        logger.warning(f"请求失败: {url}, {e}")
        return {
            "success": False,
            "html": "",
            "title": "",
            "url": url,
            "error": f"请求失败: {str(e)}",
        }
