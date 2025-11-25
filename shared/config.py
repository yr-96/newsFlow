"""
配置加载模块
提供统一的配置文件加载功能
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件
    
    参数:
        config_path: 配置文件路径，如果为None则从项目根目录查找config.yaml
    
    返回:
        配置字典
    """
    if config_path is None:
        # 尝试从项目根目录查找config.yaml
        current_dir = Path(__file__).parent
        project_root = current_dir.parent
        config_path = project_root / "config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        return {
            "output": {
                "base_dir": "./output",
                "date_format": "%Y-%m-%d"
            }
        }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config or {}
    except Exception as e:
        logger.error(f"读取配置文件失败: {str(e)}，使用默认配置")
        return {
            "output": {
                "base_dir": "./output",
                "date_format": "%Y-%m-%d"
            }
        }
