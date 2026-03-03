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
