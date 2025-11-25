"""
缓存管理模块
提供文章缓存文件的读写和管理功能
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_cache_file_path(date_folder: Path) -> Path:
    """
    获取缓存文件路径
    
    参数:
        date_folder: 日期文件夹路径
    
    返回:
        缓存文件路径（JSON文件）
    """
    return date_folder / "articles_cache.json"


def load_cache(date_folder: Path) -> Dict[str, Any]:
    """
    加载缓存文件
    
    参数:
        date_folder: 日期文件夹路径
    
    返回:
        缓存数据字典，格式为:
        {
            "articles": [
                {
                    "original_title": "原文标题",
                    "chinese_title": "中文标题",
                    "url": "链接"
                }
            ]
        }
    """
    cache_file = get_cache_file_path(date_folder)
    
    if not cache_file.exists():
        return {"articles": []}
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        return cache_data if isinstance(cache_data, dict) else {"articles": []}
    except Exception as e:
        logger.warning(f"读取缓存文件失败: {str(e)}，返回空缓存")
        return {"articles": []}


def save_cache(date_folder: Path, cache_data: Dict[str, Any]) -> bool:
    """
    保存缓存文件
    
    参数:
        date_folder: 日期文件夹路径
        cache_data: 缓存数据字典
    
    返回:
        是否保存成功
    """
    cache_file = get_cache_file_path(date_folder)
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info(f"保存缓存文件: {cache_file}")
        return True
    except Exception as e:
        logger.error(f"保存缓存文件失败: {str(e)}", exc_info=True)
        return False


def is_article_analyzed(date_folder: Path, url: str) -> bool:
    """
    检查文章是否已经分析过（通过URL判断）
    
    参数:
        date_folder: 日期文件夹路径
        url: 文章URL
    
    返回:
        是否已分析过
    """
    cache_data = load_cache(date_folder)
    articles = cache_data.get("articles", [])
    
    # 检查URL是否在缓存中
    for article in articles:
        if article.get("url") == url:
            return True
    
    return False


def add_article_to_cache(
    date_folder: Path,
    original_title: str,
    chinese_title: str,
    url: str
) -> bool:
    """
    将文章添加到缓存
    
    参数:
        date_folder: 日期文件夹路径
        original_title: 原文标题
        chinese_title: 中文标题
        url: 文章URL
    
    返回:
        是否添加成功
    """
    cache_data = load_cache(date_folder)
    articles = cache_data.get("articles", [])
    
    # 检查是否已存在（通过URL判断）
    for article in articles:
        if article.get("url") == url:
            # 已存在，更新信息
            article["original_title"] = original_title
            article["chinese_title"] = chinese_title
            return save_cache(date_folder, cache_data)
    
    # 不存在，添加新记录
    articles.append({
        "original_title": original_title,
        "chinese_title": chinese_title,
        "url": url
    })
    cache_data["articles"] = articles
    
    return save_cache(date_folder, cache_data)
