"""
链接提取模块
使用Selenium无头模式访问网站，提取所有链接
"""
import logging
import sys
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from requests.exceptions import ConnectionError as RequestsConnectionError
from bs4 import BeautifulSoup
import os
import glob

# 配置日志（输出到stderr）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def extract_links_from_url(url: str) -> Dict[str, Any]:
    """
    从指定URL提取所有链接
    
    参数:
        url: 网站URL（如 "https://example.com"）
    
    返回:
        {
            "links": ["url1", "url2", ...],
            "count": 链接数量
        }
    
    异常:
        如果访问失败，返回 {"links": [], "count": 0, "error": "错误信息"}
    """
    driver = None
    try:
        # 配置Chrome无头模式
        options = Options()
        options.add_argument("--headless")  # 无头模式，不显示浏览器窗口
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")  # 在服务器环境下可能需要
        options.add_argument("--disable-dev-shm-usage")  # 避免共享内存问题
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 创建WebDriver实例
        from selenium.webdriver.chrome.service import Service
        
        # 尝试获取ChromeDriver路径，处理网络错误
        try:
            driver_path = ChromeDriverManager().install()
        except (RequestsConnectionError, Exception) as e:
            error_msg = str(e)
            # 检查是否是网络连接错误
            if isinstance(e, RequestsConnectionError) or "Could not reach host" in error_msg or "Are you offline" in error_msg:
                # 网络连接失败，尝试使用缓存的ChromeDriver
                logger.warning(f"无法下载ChromeDriver（网络问题），尝试使用缓存的驱动...")
                cache_path = os.path.expanduser("~/.wdm/drivers/chromedriver")
                if os.path.exists(cache_path):
                    # 查找缓存目录中的最新版本
                    cached_drivers = glob.glob(f"{cache_path}/**/chromedriver*", recursive=True)
                    if cached_drivers:
                        driver_path = max(cached_drivers, key=os.path.getmtime)
                        logger.info(f"使用缓存的ChromeDriver: {driver_path}")
                    else:
                        raise Exception("无法下载ChromeDriver且没有找到缓存的驱动。请检查网络连接或手动安装ChromeDriver。")
                else:
                    raise Exception(f"无法下载ChromeDriver: {error_msg}。请检查网络连接。")
            else:
                # 其他类型的错误，直接抛出
                raise
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
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
        
        # 提取所有<a>标签的href属性
        links = []
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
            
            links.append(absolute_url)
        
        # 去重
        unique_links = list(dict.fromkeys(links))  # 保持顺序的去重
        
        logger.info(f"从 {url} 提取到 {len(unique_links)} 个链接")
        
        return {
            "links": unique_links,
            "count": len(unique_links)
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
