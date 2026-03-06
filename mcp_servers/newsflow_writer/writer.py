"""
Markdown文件写入模块（兼容层）
提供创建日期文件夹、文件名安全处理、Markdown格式生成和文件写入功能
所有实际实现已迁移到独立模块，此文件保持向后兼容性
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# 导入共享配置模块
from shared.config import load_config

# 导入各个功能模块
from .file_utils import (
    sanitize_filename,
    get_output_base_dir,
    validate_date_format,
    create_date_folder,
    append_valuable_links_to_json,
    read_valuable_links_json,
    read_articles_for_email_from_json,
    update_link_summary_in_json,
    update_link_error_in_json,
)
from .cache import (
    is_article_analyzed,
    add_article_to_cache
)
from .markdown import (
    generate_markdown_content,
    parse_markdown_file,
    read_markdown_files_from_folder,
)
from .html_generator import generate_email_html
from .email_sender import (
    normalize_recipients,
    send_email
)

logger = logging.getLogger(__name__)


def save_markdown_file(
    title: str,
    original_title: str,
    summary: str,
    url: str,
    date: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    chinese_title: Optional[str] = None,
    skip_if_exists: bool = False,
    detailed_summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    保存Markdown文件到日期文件夹
    
    参数:
        title: 文件名（文章标题，格式：中文标题（英文原标题），会进行安全处理）
        original_title: 文章原标题（格式：中文标题（英文原标题），Markdown中的"原名"）
        summary: AI生成的约200字简短摘要（Markdown中的"ai总结内容"），采用轻松、口语化的表达方式
        url: 文章原始URL（Markdown中的"原文链接"）
        date: 日期（YYYY-MM-DD格式），默认为今天
        config: 配置字典，如果为None则自动加载
        chinese_title: 中文标题（用于缓存），如果为None则使用title作为默认值
        skip_if_exists: 如果文章已分析过是否跳过保存（默认False，会覆盖保存）
        detailed_summary: 详细的文章概括（可选但推荐提供，500-800字），包含背景信息、核心要点、关键信息、影响分析和结论，按照规范应该生成且不能为空
    
    返回:
        {
            "path": "保存路径（完整路径）",
            "filename": "文件名.md",
            "date_folder": "日期文件夹路径",
            "success": true,
            "cached": false  # 是否来自缓存（文章已分析过）
        }
    """
    try:
        # 创建日期文件夹
        folder_result = create_date_folder(date, config)
        if not folder_result.get("success"):
            return {
                "path": "",
                "filename": "",
                "date_folder": "",
                "success": False,
                "error": folder_result.get("error", "创建日期文件夹失败"),
                "cached": False
            }
        
        date_folder_path = Path(folder_result["path"])
        
        # 设置中文标题（用于缓存）
        if chinese_title is None:
            chinese_title = title
        
        # 检查文章是否已经分析过
        if is_article_analyzed(date_folder_path, url):
            if skip_if_exists:
                logger.info(f"文章已分析过，跳过保存: {url}")
                return {
                    "path": "",
                    "filename": "",
                    "date_folder": str(date_folder_path),
                    "success": True,
                    "cached": True,
                    "message": "文章已分析过，已跳过保存"
                }
            else:
                logger.info(f"文章已分析过，将覆盖保存: {url}")
        
        # 文件名安全处理
        safe_filename = sanitize_filename(title)
        if not safe_filename.endswith('.md'):
            safe_filename += '.md'
        
        # 构建完整文件路径
        file_path = date_folder_path / safe_filename
        
        # 路径安全验证：确保文件路径在基础目录内
        base_dir = get_output_base_dir(config)
        try:
            file_path.resolve().relative_to(base_dir.resolve())
        except ValueError:
            return {
                "path": "",
                "filename": "",
                "date_folder": "",
                "success": False,
                "error": "路径安全验证失败：文件路径不在允许的目录内",
                "cached": False
            }
        
        # 生成Markdown内容（传入 title 用于提取中英文标题）
        markdown_content = generate_markdown_content(original_title, summary, url, detailed_summary, title)
        
        # 写入文件（覆盖模式）
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"保存Markdown文件: {file_path}")
        
        # 更新缓存：将文章信息添加到缓存
        cache_success = add_article_to_cache(
            date_folder_path,
            original_title,
            chinese_title,
            url
        )
        
        if not cache_success:
            logger.warning(f"保存缓存失败，但文件已保存: {file_path}")
        
        return {
            "path": str(file_path),
            "filename": safe_filename,
            "date_folder": str(date_folder_path),
            "success": True,
            "cached": False
        }
        
    except Exception as e:
        logger.error(f"保存Markdown文件失败: {str(e)}", exc_info=True)
        return {
            "path": "",
            "filename": "",
            "date_folder": "",
            "success": False,
            "error": str(e),
            "cached": False
        }


def send_email_from_date_folder(
    date: str,
    recipient_email: Optional[Any] = None,
    subject: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    读取指定日期文件夹中的 valuable_links.json，提取有 summary 的链接，生成 HTML 邮件并发送到指定邮箱（支持多个收件人）
    
    参数:
        date: 日期（YYYY-MM-DD格式），要读取的日期文件夹
        recipient_email: 收件人邮箱地址（可选，可以是字符串、列表或None，如果为None则从配置读取）
        subject: 邮件主题（可选），默认为"NewsFlow - {date} 新闻摘要"
        config: 配置字典（可选），如果为None则自动加载
    
    返回:
        {
            "success": True/False,
            "date": "日期",
            "emails": "收件人邮箱列表",
            "items_count": 读取的有效链接数量（有 summary 的）,
            "message": "成功/错误消息",
            "recipients": "成功发送的收件人列表",
            "failed": "发送失败的收件人列表（如果有）",
            "error": "错误信息（如果失败）"
        }
    """
    try:
        # 验证日期格式
        if not validate_date_format(date):
            recipients_str = ""
            if recipient_email:
                if isinstance(recipient_email, list):
                    recipients_str = ", ".join(recipient_email)
                else:
                    recipients_str = str(recipient_email)
            return {
                "success": False,
                "date": date,
                "emails": [],
                "items_count": 0,
                "message": f"日期格式错误，应为YYYY-MM-DD: {date}",
                "recipients": [],
                "failed": [],
                "error": "日期格式错误"
            }
        
        # 加载配置
        if config is None:
            config = load_config()
        
        # 获取收件人邮箱（优先使用参数，其次配置）
        recipients = recipient_email
        if recipients is None:
            email_config = config.get("email", {})
            # 优先使用 recipient_emails（新格式），向后兼容 recipient_email（旧格式）
            recipients = email_config.get("recipient_emails")
            if not recipients:
                recipients = email_config.get("recipient_email")  # 向后兼容
            if not recipients:
                return {
                    "success": False,
                    "date": date,
                    "emails": [],
                    "items_count": 0,
                    "message": "未指定收件人邮箱，请在参数中提供recipient_email或在config.yaml中配置email.recipient_emails",
                    "recipients": [],
                    "failed": [],
                    "error": "收件人邮箱未配置"
                }
        
        # 规范化收件人列表
        recipient_list = normalize_recipients(recipients)
        
        if not recipient_list:
            return {
                "success": False,
                "date": date,
                "emails": recipient_list,
                "items_count": 0,
                "message": "没有有效的收件人邮箱地址",
                "recipients": [],
                "failed": [],
                "error": "收件人邮箱无效"
            }
        
        # 获取日期文件夹路径
        base_dir = get_output_base_dir(config)
        date_folder = base_dir / date
        
        # 检查文件夹是否存在
        if not date_folder.exists():
            return {
                "success": False,
                "date": date,
                "emails": recipient_list,
                "items_count": 0,
                "message": f"日期文件夹不存在: {date_folder}",
                "recipients": [],
                "failed": recipient_list,
                "error": "文件夹不存在"
            }
        
        # 从 valuable_links.json 读取有 summary 的链接
        articles = read_articles_for_email_from_json(date, config)
        
        if not articles:
            return {
                "success": False,
                "date": date,
                "emails": recipient_list,
                "items_count": 0,
                "message": f"日期文件夹的 valuable_links.json 中没有找到有 summary 的链接: {date_folder}",
                "recipients": [],
                "failed": recipient_list,
                "error": "没有找到可发送的内容"
            }
        
        # 生成邮件主题
        if subject is None:
            prefix = config.get("email", {}).get("default_subject_prefix", "NewsFlow")
            subject = f"{prefix} - {date} 新闻摘要"
        
        # 生成HTML邮件正文
        html_content = generate_email_html(articles, date)
        
        # 在发送邮件前，先保存HTML文件到日期文件夹
        html_file = date_folder / f"newsflow_{date}.html"
        try:
            html_file.write_text(html_content, encoding='utf-8')
            logger.info(f"HTML文件已保存: {html_file}")
        except Exception as e:
            logger.warning(f"保存HTML文件失败: {str(e)}，继续发送邮件")
        
        # 发送邮件到所有收件人
        send_result = send_email(recipient_list, subject, html_content, config)
        
        return {
            "success": send_result.get("success", False),
            "date": date,
            "emails": recipient_list,
            "items_count": len(articles),
            "message": send_result.get("message", "邮件发送完成"),
            "recipients": send_result.get("recipients", []),
            "failed": send_result.get("failed", []),
            "error": None if send_result.get("success") else send_result.get("message", "邮件发送失败")
        }
    except Exception as e:
        logger.error(f"发送邮件功能失败: {str(e)}", exc_info=True)
        recipients_str = ""
        if recipient_email:
            if isinstance(recipient_email, list):
                recipients_str = ", ".join(recipient_email)
            else:
                recipients_str = str(recipient_email)
        return {
            "success": False,
            "date": date,
            "emails": normalize_recipients(recipient_email) if recipient_email else [],
            "items_count": 0,
            "message": f"发送邮件功能失败: {str(e)}",
            "recipients": [],
            "failed": [],
            "error": str(e)
        }


# 向后兼容：重新导出所有函数，使现有代码可以继续使用
__all__ = [
    # 配置
    'load_config',
    # 文件操作
    'sanitize_filename',
    'get_output_base_dir',
    'validate_date_format',
    'create_date_folder',
    'append_valuable_links_to_json',
    'read_valuable_links_json',
    'update_link_summary_in_json',
    'update_link_error_in_json',
    # 缓存
    'is_article_analyzed',
    'add_article_to_cache',
    # Markdown
    'generate_markdown_content',
    'parse_markdown_file',
    'read_markdown_files_from_folder',
    # HTML生成
    'generate_email_html',
    # 邮件发送
    'normalize_recipients',
    'send_email',
    # 主要功能
    'save_markdown_file',
    'send_email_from_date_folder',
]
