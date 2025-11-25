"""
Markdown相关模块
提供Markdown内容生成和解析功能
"""
import re
import logging
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


def generate_markdown_content(
    original_title: str, 
    summary: str, 
    url: str,
    detailed_summary: Optional[str] = None,
    title: Optional[str] = None
) -> str:
    """
    生成Markdown格式的内容
    
    参数:
        original_title: 文章原标题（可能是英文标题或完整标题）
        summary: AI生成的约200字简短摘要，采用轻松、口语化的表达方式
        url: 文章原始URL
        detailed_summary: 详细的文章概括（可选但推荐提供，500-800字），包含背景信息、核心要点、关键信息、影响分析和结论
        title: 完整标题（格式：中文标题（英文原标题）），用于提取中文和英文标题
    
    返回:
        Markdown格式的字符串
    """
    # 格式化原标题为 "中文标题 - 英文标题" 格式
    formatted_title = original_title  # 默认使用传入的 original_title
    
    # 如果提供了 title 参数（格式：中文标题（英文原标题）），尝试提取中英文标题
    if title:
        chinese_part = None
        english_part = None
        
        # 方法1：尝试正则表达式匹配（支持中英文括号）
        match = re.match(r'^(.+?)\s*[（(]\s*(.+?)\s*[）)]\s*$', title)
        if match:
            chinese_part = match.group(1).strip()
            english_part = match.group(2).strip()
        else:
            # 方法2：使用简单的括号分割（更宽松的匹配）
            if '(' in title:
                parts = title.split('(', 1)
                if len(parts) == 2:
                    chinese_part = parts[0].strip()
                    english_part = parts[1].rstrip(')').strip()
            elif '（' in title:
                parts = title.split('（', 1)
                if len(parts) == 2:
                    chinese_part = parts[0].strip()
                    english_part = parts[1].rstrip('）').strip()
            else:
                # 方法3：title 包含中文但没有括号，使用 title 作为中文标题
                if any('\u4e00' <= char <= '\u9fff' for char in title):
                    chinese_part = title.strip()
                    english_part = original_title.strip() if original_title else None
        
        # 如果成功提取了中文和英文部分，格式化
        if chinese_part and english_part:
            formatted_title = f"{chinese_part} - {english_part}"
        elif chinese_part:
            # 只有中文部分，尝试使用 original_title 作为英文部分
            if original_title and original_title != chinese_part:
                formatted_title = f"{chinese_part} - {original_title}"
            else:
                formatted_title = chinese_part
    
    lines = [
        "**原名**",
        formatted_title,
        "",
        "**ai总结内容**",
        summary,
        ""
    ]
    
    # 如果有详细概括，添加新部分
    if detailed_summary:
        lines.extend([
            "**详细概括**",
            detailed_summary,
            ""
        ])
    
    lines.extend([
        "**原文链接**",
        f"[{formatted_title}]({url})"
    ])
    
    return "\n".join(lines)


def parse_markdown_file(file_path: Path) -> Optional[Dict[str, str]]:
    """
    解析Markdown文件，提取文章信息
    
    参数:
        file_path: Markdown文件路径
    
    返回:
        {
            "original_title": "文章原标题",
            "summary": "AI总结内容",
            "detailed_summary": "详细概括（可选）",
            "url": "原文链接URL",
            "filename": "文件名"
        } 或 None（如果解析失败）
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        original_title = ""
        summary = ""
        detailed_summary = ""
        url = ""
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 查找"原名"
            if line == "**原名**" and i + 1 < len(lines):
                original_title = lines[i + 1].strip()
                i += 2
                continue
            
            # 查找"ai总结内容"
            if line == "**ai总结内容**" and i + 1 < len(lines):
                # 收集总结内容（可能多行）
                summary_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("**"):
                    if lines[i].strip():
                        summary_lines.append(lines[i].strip())
                    i += 1
                summary = "\n".join(summary_lines)
                continue
            
            # 查找"详细概括"
            if line == "**详细概括**" and i + 1 < len(lines):
                # 收集详细概括内容（可能多行）
                # 注意：详细概括内容本身可能包含 **背景信息**、**核心要点** 等标记
                # 所以我们应该只停止在遇到 **原文链接** 时
                detailed_lines = []
                i += 1
                while i < len(lines):
                    current_line = lines[i].strip()
                    # 只有遇到 **原文链接** 时才停止（这是最后一个字段）
                    if current_line == "**原文链接**":
                        break
                    # 如果遇到其他已知字段标记（理论上不应该，但作为安全措施）
                    if current_line in ["**原名**", "**ai总结内容**"]:
                        break
                    # 收集这一行（即使是空行或包含 ** 的内容）
                    if current_line or (not current_line and detailed_lines):  # 保留空行如果已经有内容
                        detailed_lines.append(lines[i])  # 保留原始行，不strip，保持格式
                    i += 1
                detailed_summary = "\n".join(detailed_lines).strip()
                continue
            
            # 查找"原文链接"
            if line == "**原文链接**" and i + 1 < len(lines):
                link_line = lines[i + 1].strip()
                # 处理Markdown链接格式 [text](url) 或直接URL
                if link_line.startswith('[') and '](' in link_line:
                    # Markdown格式：[title](url)
                    match = re.search(r'\]\((.*?)\)', link_line)
                    if match:
                        url = match.group(1)
                else:
                    # 直接URL
                    url = link_line
                break
            
            i += 1
        
        if not original_title or not summary:
            logger.warning(f"解析Markdown文件失败，缺少必要字段: {file_path}")
            return None
        
        result = {
            "original_title": original_title,
            "summary": summary,
            "url": url,
            "filename": file_path.name
        }
        
        # 如果有详细概括，添加到结果中
        if detailed_summary:
            result["detailed_summary"] = detailed_summary
        
        return result
    except Exception as e:
        logger.error(f"解析Markdown文件失败: {file_path}, 错误: {str(e)}", exc_info=True)
        return None


def read_markdown_files_from_folder(folder_path: Path) -> List[Dict[str, str]]:
    """
    读取文件夹中的所有Markdown文件并解析
    
    参数:
        folder_path: 日期文件夹路径
    
    返回:
        文章信息列表
    """
    articles = []
    
    if not folder_path.exists():
        logger.warning(f"文件夹不存在: {folder_path}")
        return articles
    
    # 获取所有.md文件（排除缓存文件等）
    md_files = sorted([f for f in folder_path.glob("*.md") if f.name != "articles_cache.json"])
    
    if not md_files:
        logger.warning(f"文件夹中没有找到Markdown文件: {folder_path}")
        return articles
    
    for md_file in md_files:
        article = parse_markdown_file(md_file)
        if article:
            articles.append(article)
        else:
            logger.warning(f"跳过无法解析的文件: {md_file}")
    
    return articles
