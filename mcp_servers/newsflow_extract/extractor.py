"""
链接提取模块
使用Selenium无头模式访问网站，提取所有链接
"""
import logging
import sys
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException

from .chrome_options import build_chrome_options
from bs4 import BeautifulSoup

# 配置日志（输出到stderr）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def extract_links_from_url(url: str) -> Dict[str, Any]:
    """
    从指定URL提取所有有内容的链接
    
    参数:
        url: 网站URL（如 "https://example.com"）
    
    返回:
        {
            "links": [
                {"url": "url1", "text": "链接文本内容"},
                {"url": "url2", "text": "另一个链接文本"},
                ...
            ],
            "count": 链接数量
        }
    
    说明:
        - 仅返回有文本内容的 <a> 标签（过滤空链接）
        - 每个链接携带其 a 标签对应的文本内容，便于识别有价值内容
    
    异常:
        如果访问失败，返回 {"links": [], "count": 0, "error": "错误信息"}
    """
    driver = None
    try:
        options = build_chrome_options(headless=True)
        # 使用 Selenium 4.6+ 内置 Selenium Manager 自动匹配 Chrome / ChromeDriver，勿手动指定 Service(path)
        driver = webdriver.Chrome(options=options)
        
        # 设置隐式等待
        driver.implicitly_wait(5)
        
        # 访问URL
        logger.info(f"访问URL: {url}")
        driver.get(url)
        
        # 等待页面渲染（额外等待确保JS执行完成）
        import time
        time.sleep(2)  # 等待2秒，确保动态内容加载
        
        # 获取渲染后的HTML
        html = driver.page_source
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取所有有内容的 <a> 标签，携带链接文本
        links = []
        seen_urls = set()
        base_url = url

        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').strip()
            if not href:
                continue

            # 过滤特殊链接
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue

            # 转换为绝对路径
            absolute_url = urljoin(base_url, href)

            # 验证URL格式
            parsed = urlparse(absolute_url)
            if not parsed.scheme or not parsed.netloc:
                continue

            # 只保留HTTP/HTTPS链接
            if parsed.scheme not in ('http', 'https'):
                continue

            # 提取 a 标签的文本内容
            link_text = a_tag.get_text(separator=' ', strip=True)

            # 仅保留有内容的链接
            if not link_text:
                continue

            # 去重：同一 URL 只保留首次出现（携带其文本）
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            links.append({
                "url": absolute_url,
                "text": link_text,
            })

        logger.info(f"从 {url} 提取到 {len(links)} 个有内容链接")

        return {
            "links": links,
            "count": len(links),
        }
        
    except TimeoutException as e:
        logger.error(f"访问 {url} 超时: {str(e)}")
        return {
            "links": [],
            "count": 0,
            "error": f"访问超时: {str(e)}"
        }
    except WebDriverException as e:
        logger.error(f"WebDriver错误 {url}: {str(e)}")
        return {
            "links": [],
            "count": 0,
            "error": f"浏览器错误: {str(e)}"
        }
    except Exception as e:
        logger.error(f"提取链接失败 {url}: {str(e)}", exc_info=True)
        return {
            "links": [],
            "count": 0,
            "error": f"提取失败: {str(e)}"
        }
    finally:
        # 确保关闭浏览器
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {str(e)}")
