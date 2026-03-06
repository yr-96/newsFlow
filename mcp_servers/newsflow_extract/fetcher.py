"""
页面内容获取模块
使用 Selenium 无头浏览器从 URL 获取渲染后的 HTML 内容
"""
import html as html_module
import logging
import os
import sys
import time
from typing import Dict, Any

import glob
from bs4 import BeautifulSoup

from .html_rag.html_parser import parse_and_clean_html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from requests.exceptions import ConnectionError as RequestsConnectionError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def _create_chrome_driver(timeout: int = 30):
    """创建 Chrome 无头浏览器实例（与 extractor 相同方式）"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        driver_path = ChromeDriverManager().install()
    except (RequestsConnectionError, Exception) as e:
        error_msg = str(e)
        if isinstance(e, RequestsConnectionError) or "Could not reach host" in error_msg or "Are you offline" in error_msg:
            logger.warning("无法下载 ChromeDriver（网络问题），尝试使用缓存的驱动...")
            cache_path = os.path.expanduser("~/.wdm/drivers/chromedriver")
            if os.path.exists(cache_path):
                cached_drivers = glob.glob(f"{cache_path}/**/chromedriver*", recursive=True)
                if cached_drivers:
                    driver_path = max(cached_drivers, key=os.path.getmtime)
                    logger.info(f"使用缓存的 ChromeDriver: {driver_path}")
                else:
                    raise Exception("无法下载 ChromeDriver 且没有找到缓存的驱动。请检查网络连接或手动安装 ChromeDriver。")
            else:
                raise Exception(f"无法下载 ChromeDriver: {error_msg}。请检查网络连接。")
        else:
            raise

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    driver.set_page_load_timeout(timeout)
    return driver


def _build_cleaned_html(parsed: Dict[str, Any], title: str) -> str:
    """从 parse_and_clean_html 的结果构建只含正文的简洁 HTML"""
    escaped_title = html_module.escape(title or "", quote=True)
    head = f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{escaped_title}</title></head><body>'

    structure = parsed.get("structure", [])
    if structure:
        parts = []
        for item in structure:
            tag = item.get("type", "p")
            text = item.get("text", "")
            if not text.strip():
                continue
            escaped = html_module.escape(text)
            if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "li", "article", "main", "section","pre","code",'span'):
                parts.append(f"<{tag}>{escaped}</{tag}>")
            else:
                parts.append(f"<p>{escaped}</p>")
        body = "\n".join(parts)
    else:
        text = parsed.get("text", "")
        escaped = html_module.escape(text)
        body = f"<article><pre>{escaped}</pre></article>"

    return head + body + "</body></html>"


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

    使用 Selenium 无头浏览器获取页面，支持 JS 渲染的动态页面。
    与 extract_links_from_url 采用相同方式，适用于文章、博客、GitHub 等。

    参数:
        url: 页面 URL（如文章链接、GitHub 仓库等）
        timeout: 页面加载超时秒数

    返回:
        {
            "success": bool,
            "html": str,           # 清理后的 HTML（仅含正文，已去除 script/style/nav/footer 等）
            "title": str,          # 页面标题（从 <title> 或 h1 提取）
            "url": str,            # 实际请求的 URL（可能经过重定向）
            "status_code": int,    # 成功时为 200
            "error": str           # 错误信息（失败时）
        }
    """
    if not url or not url.strip():
        return {
            "success": False,
            "html": "",
            "title": "",
            "url": url or "",
            "status_code": 0,
            "error": "URL 不能为空",
        }

    url = url.strip()
    driver = None

    try:
        driver = _create_chrome_driver(timeout=timeout)

        logger.info(f"访问 URL: {url}")
        driver.get(url)

        # 等待页面渲染（与 extractor 相同）
        time.sleep(2)

        raw_html = driver.page_source
        actual_url = driver.current_url
        title = _extract_title_from_html(raw_html, url)

        # 调用 parse_and_clean_html 去除与正文无关的内容
        parsed = parse_and_clean_html(raw_html)
        if parsed.get("success"):
            html = _build_cleaned_html(parsed, title)
            logger.info(f"从 {url} 获取 HTML 成功，已清理，长度 {len(html)} 字符（原始 {len(raw_html)} 字符）")
        else:
            html = raw_html
            logger.warning(f"HTML 清理失败，返回原始内容: {parsed.get('error')}")

        return {
            "success": True,
            "html": html,
            "title": title,
            "url": actual_url,
            "status_code": 200,
            "error": None,
        }

    except TimeoutException as e:
        logger.warning(f"页面加载超时: {url}, {e}")
        return {
            "success": False,
            "html": "",
            "title": "",
            "url": url,
            "status_code": 0,
            "error": f"请求超时（{timeout}秒）",
        }
    except WebDriverException as e:
        logger.warning(f"浏览器错误: {url}, {e}")
        return {
            "success": False,
            "html": "",
            "title": "",
            "url": url,
            "status_code": 0,
            "error": f"浏览器错误: {str(e)}",
        }
    except Exception as e:
        logger.warning(f"获取 HTML 失败: {url}, {e}", exc_info=True)
        return {
            "success": False,
            "html": "",
            "title": "",
            "url": url,
            "status_code": 0,
            "error": f"获取失败: {str(e)}",
        }
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")
