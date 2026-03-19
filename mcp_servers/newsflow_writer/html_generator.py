"""
HTML生成模块
提供邮件HTML内容生成功能
"""
import logging
from typing import List, Dict

# Markdown转HTML
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logging.warning("markdown 库未安装，detailed_summary 将显示为纯文本格式。请运行: pip install markdown")

logger = logging.getLogger(__name__)


def generate_email_html(articles: List[Dict[str, str]], date: str) -> str:
    """
    生成HTML格式的邮件正文
    
    参数:
        articles: 文章信息列表
        date: 日期字符串（YYYY-MM-DD）
    
    返回:
        HTML格式的邮件正文
    """
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 10px;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            max-width: 800px;
            margin: 0 auto;
            width: 100%;
        }}
        h1 {{
            color: #1a202c;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .meta {{
            color: #718096;
            margin-bottom: 32px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .meta::before {{
            content: "📰";
            font-size: 16px;
        }}
        .article {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: all 0.3s ease;
            position: relative;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .article:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border-color: #cbd5e0;
            transform: translateY(-2px);
        }}
        @media (hover: none) {{
            .article:hover {{
                transform: none;
            }}
        }}
        .article::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px 0 0 10px;
        }}
        .article-title {{
            color: #1a202c;
            font-size: 22px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.4;
            padding-left: 4px;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .article-original-title {{
            color: #718096;
            font-size: 14px;
            margin-bottom: 16px;
            font-weight: 400;
            line-height: 1.4;
        }}
        .article-summary {{
            color: #4a5568;
            margin: 16px 0;
            line-height: 1.8;
            white-space: pre-wrap;
            padding: 16px;
            background: #f7fafc;
            border-radius: 8px;
            border-left: 3px solid #e2e8f0;
            word-wrap: break-word;
            overflow-wrap: break-word;
            font-size: 15px;
        }}
        .article-actions {{
            margin-top: 20px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
        }}
        .article-link {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            text-decoration: none;
            font-weight: 500;
            border-radius: 8px;
            font-size: 15px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
            min-height: 44px;
            justify-content: center;
            touch-action: manipulation;
            -webkit-tap-highlight-color: transparent;
        }}
        .article-link:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
            text-decoration: none;
        }}
        .article-link:active {{
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
        }}
        /* 详细概括直接显示样式 */
        .detail-content {{
            margin-top: 20px;
            padding: 24px;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 10px;
            border: 2px solid #e2e8f0;
            border-left: 4px solid #667eea;
            line-height: 1.8;
            color: #4a5568;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            word-wrap: break-word;
            overflow-wrap: break-word;
            font-size: 15px;
            position: relative;
        }}
        .detail-content::before {{
            content: "📋 详细概括";
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .detail-content h2, .detail-content h3, .detail-content h4 {{
            color: #1a202c;
            margin-top: 20px;
            margin-bottom: 12px;
            font-weight: 600;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .detail-content h2 {{
            font-size: 20px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
        }}
        .detail-content h3 {{
            font-size: 18px;
        }}
        .detail-content h4 {{
            font-size: 16px;
        }}
        .detail-content p {{
            margin: 12px 0;
            color: #4a5568;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .detail-content ul, .detail-content ol {{
            margin: 12px 0;
            padding-left: 24px;
            color: #4a5568;
        }}
        .detail-content li {{
            margin: 6px 0;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .detail-content strong {{
            color: #2d3748;
            font-weight: 600;
        }}
        .detail-content em {{
            color: #4a5568;
            font-style: italic;
        }}
        .footer {{
            margin-top: 48px;
            padding-top: 24px;
            border-top: 2px solid #e2e8f0;
            text-align: center;
            color: #a0aec0;
            font-size: 13px;
        }}
        /* 平板设备适配 */
        @media (max-width: 768px) {{
            body {{
                padding: 8px;
            }}
            .container {{
                padding: 28px;
                border-radius: 8px;
            }}
            h1 {{
                font-size: 24px;
            }}
            .article-title {{
                font-size: 20px;
            }}
        }}
        
        /* 移动设备适配 */
        @media (max-width: 600px) {{
            body {{
                padding: 0;
                background: #ffffff;
            }}
            .container {{
                padding: 16px;
                border-radius: 0;
                box-shadow: none;
                max-width: 100%;
            }}
            h1 {{
                font-size: 22px;
                margin-bottom: 6px;
            }}
            .meta {{
                margin-bottom: 20px;
                font-size: 13px;
            }}
            .article {{
                padding: 16px;
                margin-bottom: 16px;
                border-radius: 8px;
            }}
            .article::before {{
                width: 3px;
            }}
            .article-title {{
                font-size: 18px;
                margin-bottom: 12px;
                padding-left: 2px;
            }}
            .article-summary {{
                padding: 12px;
                margin: 12px 0;
                font-size: 14px;
                line-height: 1.7;
                border-left-width: 2px;
            }}
            .article-actions {{
                flex-direction: column;
                align-items: stretch;
                gap: 10px;
                margin-top: 16px;
            }}
            .article-link {{
                width: 100%;
                justify-content: center;
                padding: 14px 20px;
                font-size: 15px;
                min-height: 48px;
            }}
            .detail-content {{
                padding: 16px;
                margin-top: 12px;
                font-size: 14px;
                line-height: 1.7;
            }}
            .detail-content h2 {{
                font-size: 18px;
                margin-top: 16px;
                margin-bottom: 10px;
            }}
            .detail-content h3 {{
                font-size: 16px;
                margin-top: 14px;
                margin-bottom: 8px;
            }}
            .detail-content h4 {{
                font-size: 15px;
                margin-top: 12px;
                margin-bottom: 6px;
            }}
            .detail-content p {{
                margin: 10px 0;
                font-size: 14px;
            }}
            .detail-content ul, .detail-content ol {{
                padding-left: 20px;
                margin: 10px 0;
            }}
            .detail-content li {{
                margin: 4px 0;
            }}
            .footer {{
                margin-top: 32px;
                padding-top: 20px;
                font-size: 12px;
            }}
        }}
        
        /* 小屏幕移动设备 */
        @media (max-width: 400px) {{
            .container {{
                padding: 12px;
            }}
            h1 {{
                font-size: 20px;
            }}
            .article {{
                padding: 12px;
            }}
            .article-title {{
                font-size: 17px;
            }}
            .article-summary {{
                padding: 10px;
                font-size: 13px;
            }}
            .detail-content {{
                padding: 12px;
                font-size: 13px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NewsFlow - {date} 新闻摘要</h1>
        <div class="meta">共 {count} 篇文章</div>
        {articles_html}
        <div class="footer">
            <p>本邮件由 NewsFlow 自动生成</p>
        </div>
    </div>
</body>
</html>"""
    
    articles_html = ""
    for index, article in enumerate(articles):
        title = article.get("title", "未知标题")
        original_title = article.get("original_title", "未知标题")
        summary = article.get("summary", "")
        detailed_summary = article.get("detailed_summary", "")
        url = article.get("url", "#")
        
        # 转义HTML特殊字符
        title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        summary = summary.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # 将 detailed_summary 从 Markdown 转换为 HTML
        if detailed_summary:
            if MARKDOWN_AVAILABLE:
                try:
                    # 转换 Markdown 为 HTML
                    md = markdown.Markdown(extensions=['extra', 'nl2br'])
                    detailed_summary_html = md.convert(detailed_summary)
                except Exception as e:
                    logger.error(f"Markdown转换失败: {e}，使用转义的纯文本")
                    # 如果转换失败，回退到转义纯文本
                    detailed_summary_html = detailed_summary.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    # 简单的换行转换
                    detailed_summary_html = detailed_summary_html.replace("\n", "<br>")
            else:
                # 如果没有 markdown 库，使用简单的转义和换行处理
                detailed_summary_html = detailed_summary.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                # 简单的换行转换
                detailed_summary_html = detailed_summary_html.replace("\n", "<br>")
        else:
            detailed_summary_html = ""
        
        article_html = f"""
        <div class="article">
            <div class="article-title">{title}</div>
            <div class="article-original-title">{original_title}</div>
            <div class="article-summary">{summary}</div>
"""
        
        # 如果有详细概括，直接显示（使用内联样式确保邮件客户端兼容）
        if detailed_summary_html:
            article_html += f"""                <div style="margin-top: 20px; padding: 20px; background-color: #f8fafc; border: 2px solid #e2e8f0; border-left: 4px solid #667eea; border-radius: 8px; line-height: 1.8; color: #4a5568; font-size: 15px;">
                    <div style="font-size: 13px; font-weight: 600; color: #667eea; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 2px solid #e2e8f0;">📋 详细概括</div>
                    {detailed_summary_html}
                </div>
"""
        
        article_html += f"""            <div class="article-actions">
                <a href="{url}" class="article-link" target="_blank">阅读原文 →</a>
            </div>
        </div>
        """
        articles_html += article_html
    
    return html_template.format(
        date=date,
        count=len(articles),
        articles_html=articles_html
    )

