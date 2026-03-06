"""
文件操作工具模块
提供文件名安全处理、日期文件夹创建、有价值链接JSON管理等功能
"""
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from shared.config import load_config

logger = logging.getLogger(__name__)

# 有价值链接 JSON 文件名
VALUABLE_LINKS_JSON = "valuable_links.json"


def sanitize_filename(filename: str) -> str:
    """
    文件名安全处理：去除或替换特殊字符，限制长度
    
    参数:
        filename: 原始文件名
    
    返回:
        处理后的安全文件名
    """
    # 移除或替换不允许的字符（Windows系统限制）
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 移除前后空格和点
    filename = filename.strip('. ')
    
    # 限制长度（保留扩展名的空间）
    if len(filename) > 100:
        filename = filename[:100]
    
    # 如果文件名为空，使用默认名称
    if not filename:
        filename = "untitled"
    
    return filename


def get_output_base_dir(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    获取输出基础目录路径
    
    参数:
        config: 配置字典，如果为None则自动加载
    
    返回:
        输出基础目录的Path对象
    """
    if config is None:
        config = load_config()
    
    base_dir = config.get("output", {}).get("base_dir", "./output")
    base_path = Path(base_dir)
    
    # 如果是相对路径，转换为相对于项目根目录的绝对路径
    if not base_path.is_absolute():
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        base_path = project_root / base_path
    
    return base_path.resolve()


def validate_date_format(date_str: str) -> bool:
    """
    验证日期格式是否为YYYY-MM-DD
    
    参数:
        date_str: 日期字符串
    
    返回:
        是否为有效格式
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def create_date_folder(date: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    创建日期文件夹
    
    参数:
        date: 日期字符串（YYYY-MM-DD格式），如果为None则使用今天
        config: 配置字典，如果为None则自动加载
    
    返回:
        {
            "path": "文件夹完整路径",
            "success": true
        }
    """
    try:
        # 获取日期
        if date is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            if not validate_date_format(date):
                return {
                    "path": "",
                    "success": False,
                    "error": f"日期格式错误，应为YYYY-MM-DD: {date}"
                }
            date_str = date
        
        # 获取基础目录
        base_dir = get_output_base_dir(config)
        
        # 构建日期文件夹路径
        date_folder = base_dir / date_str
        
        # 创建文件夹（如果不存在）
        date_folder.mkdir(parents=True, exist_ok=True)
        
        # 在文件夹中创建 valuable_links.json（如果不存在）
        _init_valuable_links_json(date_folder)
        
        logger.info(f"创建日期文件夹: {date_folder}")
        
        return {
            "path": str(date_folder),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"创建日期文件夹失败: {str(e)}", exc_info=True)
        return {
            "path": "",
            "success": False,
            "error": str(e)
        }


def _init_valuable_links_json(date_folder: Path) -> None:
    """
    在日期文件夹中初始化 valuable_links.json 文件（如果不存在）
    结构：数组，每项为 { "source_site": "源网站", "url": "...", "text": "..." }
    
    参数:
        date_folder: 日期文件夹路径
    """
    json_path = date_folder / VALUABLE_LINKS_JSON
    if not json_path.exists():
        initial_data: List[Dict[str, Any]] = []
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
        logger.info(f"初始化有价值链接JSON: {json_path}")


def append_valuable_links_to_json(
    date: str,
    site_name: str,
    links: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    将指定网站的有价值链接追加到日期文件夹中的 valuable_links.json
    
    参数:
        date: 日期（YYYY-MM-DD格式）
        site_name: 来源网站名称（如 "Hacker News"、"TLDR"、"GitHub Trending"）
        links: 有价值链接数组，每项应包含 url 和 text，如 [{"url": "...", "text": "..."}]
        config: 配置字典，如果为None则自动加载
    
    返回:
        {
            "success": true/false,
            "date_folder": "日期文件夹路径",
            "site_name": "网站名称",
            "links_count": 追加的链接数量,
            "error": "错误信息（如果失败）"
        }
    """
    try:
        if not validate_date_format(date):
            return {
                "success": False,
                "date_folder": "",
                "site_name": site_name,
                "links_count": 0,
                "error": f"日期格式错误，应为YYYY-MM-DD: {date}"
            }
        
        if config is None:
            config = load_config()
        
        base_dir = get_output_base_dir(config)
        date_folder = base_dir / date
        
        if not date_folder.exists():
            return {
                "success": False,
                "date_folder": str(date_folder),
                "site_name": site_name,
                "links_count": 0,
                "error": f"日期文件夹不存在: {date_folder}"
            }
        
        json_path = date_folder / VALUABLE_LINKS_JSON
        if not json_path.exists():
            _init_valuable_links_json(date_folder)
        
        # 读取现有数据（数组结构）
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 兼容旧格式：如果是对象则转为数组
        if isinstance(data, dict):
            all_items = []
            if "all_links" in data:
                all_items = data["all_links"]
            elif "sites" in data:
                for sname, slinks in data["sites"].items():
                    for link in slinks:
                        all_items.append({
                            "source_site": sname,
                            "url": link.get("url", ""),
                            "text": link.get("text", "")
                        })
            data = all_items
        elif not isinstance(data, list):
            data = []
        
        # 规范化 links：每项包含 source_site、url、text
        existing_urls = {item["url"] for item in data if isinstance(item, dict) and item.get("url")}
        appended_count = 0
        for item in links:
            if isinstance(item, dict) and item.get("url"):
                url = str(item["url"])
                if url not in existing_urls:
                    data.append({
                        "source_site": site_name,
                        "url": url,
                        "text": str(item.get("text", ""))
                    })
                    existing_urls.add(url)
                    appended_count += 1
        
        # 写回文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"追加有价值链接到 {json_path}: {site_name}, {appended_count} 条")
        
        return {
            "success": True,
            "date_folder": str(date_folder),
            "site_name": site_name,
            "links_count": appended_count
        }
        
    except Exception as e:
        logger.error(f"追加有价值链接失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "date_folder": "",
            "site_name": site_name,
            "links_count": 0,
            "error": str(e)
        }


def read_valuable_links_json(
    date: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    从日期文件夹中读取 valuable_links.json，返回链接列表
    
    参数:
        date: 日期（YYYY-MM-DD格式）
        config: 配置字典，如果为None则自动加载
    
    返回:
        {
            "success": true/false,
            "links": [{"source_site", "url", "text", "summary": {...}?, "error": "..."?}, ...],
            "date_folder": "日期文件夹路径",
            "error": "错误信息（如果失败）"
        }
    """
    try:
        if not validate_date_format(date):
            return {
                "success": False,
                "links": [],
                "date_folder": "",
                "error": f"日期格式错误，应为YYYY-MM-DD: {date}"
            }
        
        if config is None:
            config = load_config()
        
        base_dir = get_output_base_dir(config)
        date_folder = base_dir / date
        
        if not date_folder.exists():
            return {
                "success": False,
                "links": [],
                "date_folder": str(date_folder),
                "error": f"日期文件夹不存在: {date_folder}"
            }
        
        json_path = date_folder / VALUABLE_LINKS_JSON
        if not json_path.exists():
            return {
                "success": True,
                "links": [],
                "date_folder": str(date_folder)
            }
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            all_items = []
            if "all_links" in data:
                all_items = data["all_links"]
            elif "sites" in data:
                for sname, slinks in data["sites"].items():
                    for link in slinks:
                        all_items.append({
                            "source_site": sname,
                            "url": link.get("url", ""),
                            "text": link.get("text", ""),
                            **{k: v for k, v in link.items() if k not in ("url", "text")}
                        })
            data = all_items
        elif not isinstance(data, list):
            data = []
        
        return {
            "success": True,
            "links": data,
            "date_folder": str(date_folder)
        }
        
    except Exception as e:
        logger.error(f"读取有价值链接JSON失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "links": [],
            "date_folder": "",
            "error": str(e)
        }


def read_articles_for_email_from_json(
    date: str,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    从日期文件夹的 valuable_links.json 中读取有 summary 的链接，转换为邮件所需的文章格式
    
    参数:
        date: 日期（YYYY-MM-DD格式）
        config: 配置字典，如果为None则自动加载
    
    返回:
        文章列表，每项包含 original_title, summary, detailed_summary, url
        仅包含有 summary 的链接，跳过有 error 的
    """
    result = read_valuable_links_json(date, config)
    if not result.get("success"):
        return []
    links = result.get("links", [])
    articles = []
    for link in links:
        if "summary" not in link or not isinstance(link.get("summary"), dict):
            continue
        s = link["summary"]
        articles.append({
            "original_title": s.get("original_title", link.get("text", "未知标题")),
            "summary": s.get("summary", ""),
            "detailed_summary": s.get("detailed_summary", ""),
            "url": link.get("url", "#"),
        })
    return articles


def update_link_summary_in_json(
    date: str,
    url: str,
    title: str,
    original_title: str,
    summary: str,
    detailed_summary: str,
    skip_if_exists: bool = True,
    date_str: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    将链接的总结数据写入 valuable_links.json 中对应链接对象下
    
    在 JSON 中查找 url 匹配的链接，为其添加 summary 对象，包含：
    title, original_title, summary, detailed_summary, date
    
    参数:
        date: 日期（YYYY-MM-DD格式），用于定位日期文件夹
        url: 链接URL，用于匹配要更新的链接
        title: 内容标题（格式：中文标题（英文原标题/项目名））
        original_title: 内容原标题（格式：中文标题（英文原标题/项目名））
        summary: AI生成的200字简短摘要
        detailed_summary: AI生成的500-800字详细概括
        skip_if_exists: 如果该链接已有 summary 则跳过（默认True）
        date_str: 总结日期（YYYY-MM-DD），可选，默认为 date 参数
        config: 配置字典，如果为None则自动加载
    
    返回:
        {
            "success": true/false,
            "updated": true/false,  # 是否实际更新了（skip时为false）
            "date_folder": "日期文件夹路径",
            "url": "链接URL",
            "error": "错误信息（如果失败）"
        }
    """
    try:
        if not validate_date_format(date):
            return {
                "success": False,
                "updated": False,
                "date_folder": "",
                "url": url,
                "error": f"日期格式错误，应为YYYY-MM-DD: {date}"
            }
        
        if config is None:
            config = load_config()
        
        base_dir = get_output_base_dir(config)
        date_folder = base_dir / date
        
        if not date_folder.exists():
            return {
                "success": False,
                "updated": False,
                "date_folder": str(date_folder),
                "url": url,
                "error": f"日期文件夹不存在: {date_folder}"
            }
        
        json_path = date_folder / VALUABLE_LINKS_JSON
        if not json_path.exists():
            return {
                "success": False,
                "updated": False,
                "date_folder": str(date_folder),
                "url": url,
                "error": f"valuable_links.json 不存在: {json_path}"
            }
        
        summary_date = date_str or date
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            all_items = []
            if "all_links" in data:
                all_items = data["all_links"]
            elif "sites" in data:
                for sname, slinks in data["sites"].items():
                    for link in slinks:
                        all_items.append({
                            "source_site": sname,
                            "url": link.get("url", ""),
                            "text": link.get("text", ""),
                            **{k: v for k, v in link.items() if k not in ("url", "text")}
                        })
            data = all_items
        elif not isinstance(data, list):
            data = []
        
        def _normalize_url(u: str) -> str:
            u = (u or "").strip()
            if "?" in u:
                u = u.split("?")[0]
            if "#" in u:
                u = u.split("#")[0]
            return u.rstrip("/")

        url_normalized = _normalize_url(url)
        updated = False
        for item in data:
            if isinstance(item, dict) and _normalize_url(item.get("url", "")) == url_normalized:
                if skip_if_exists and item.get("summary"):
                    return {
                        "success": True,
                        "updated": False,
                        "date_folder": str(date_folder),
                        "url": url
                    }
                item.pop("error", None)  # 成功写入 summary 时移除旧错误
                item["summary"] = {
                    "title": title,
                    "original_title": original_title,
                    "summary": summary,
                    "detailed_summary": detailed_summary,
                    "date": summary_date
                }
                updated = True
                break
        
        if not updated:
            return {
                "success": False,
                "updated": False,
                "date_folder": str(date_folder),
                "url": url,
                "error": f"未找到匹配的链接: {url}"
            }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"更新链接总结到 {json_path}: {url[:50]}...")
        
        return {
            "success": True,
            "updated": True,
            "date_folder": str(date_folder),
            "url": url
        }
        
    except Exception as e:
        logger.error(f"更新链接总结失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "updated": False,
            "date_folder": "",
            "url": url,
            "error": str(e)
        }


def update_link_error_in_json(
    date: str,
    url: str,
    error_message: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    将链接处理失败时的错误信息写入 valuable_links.json 中对应链接对象下
    
    参数:
        date: 日期（YYYY-MM-DD格式）
        url: 链接URL
        error_message: 错误描述
    
    返回:
        同 update_link_summary_in_json
    """
    try:
        if not validate_date_format(date):
            return {
                "success": False,
                "updated": False,
                "date_folder": "",
                "url": url,
                "error": f"日期格式错误，应为YYYY-MM-DD: {date}"
            }
        
        if config is None:
            config = load_config()
        
        base_dir = get_output_base_dir(config)
        date_folder = base_dir / date
        
        if not date_folder.exists():
            return {
                "success": False,
                "updated": False,
                "date_folder": str(date_folder),
                "url": url,
                "error": f"日期文件夹不存在: {date_folder}"
            }
        
        json_path = date_folder / VALUABLE_LINKS_JSON
        if not json_path.exists():
            return {
                "success": False,
                "updated": False,
                "date_folder": str(date_folder),
                "url": url,
                "error": f"valuable_links.json 不存在: {json_path}"
            }
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            all_items = []
            if "all_links" in data:
                all_items = data["all_links"]
            elif "sites" in data:
                for sname, slinks in data["sites"].items():
                    for link in slinks:
                        all_items.append({
                            "source_site": sname,
                            "url": link.get("url", ""),
                            "text": link.get("text", ""),
                            **{k: v for k, v in link.items() if k not in ("url", "text")}
                        })
            data = all_items
        elif not isinstance(data, list):
            data = []
        
        def _normalize_url(u: str) -> str:
            u = (u or "").strip()
            if "?" in u:
                u = u.split("?")[0]
            if "#" in u:
                u = u.split("#")[0]
            return u.rstrip("/")

        url_normalized = _normalize_url(url)
        updated = False
        for item in data:
            if isinstance(item, dict) and _normalize_url(item.get("url", "")) == url_normalized:
                item["error"] = error_message
                updated = True
                break
        
        if not updated:
            return {
                "success": False,
                "updated": False,
                "date_folder": str(date_folder),
                "url": url,
                "error": f"未找到匹配的链接: {url}"
            }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"记录链接错误到 {json_path}: {url[:50]}... - {error_message}")
        
        return {
            "success": True,
            "updated": True,
            "date_folder": str(date_folder),
            "url": url
        }
        
    except Exception as e:
        logger.error(f"记录链接错误失败: {str(e)}", exc_info=True)
        return {
            "success": False,
            "updated": False,
            "date_folder": "",
            "url": url,
            "error": str(e)
        }
