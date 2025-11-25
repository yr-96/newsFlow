"""
文件操作工具模块
提供文件名安全处理、日期文件夹创建等功能
"""
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from shared.config import load_config

logger = logging.getLogger(__name__)


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
