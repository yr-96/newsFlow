#!/usr/bin/env python3
"""
生成HTML邮件内容但不发送邮件
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_servers.newsflow_writer.writer import (
    read_markdown_files_from_folder,
    generate_email_html,
    get_output_base_dir,
    load_config
)

def main():
    """生成HTML文件"""
    # 读取配置
    config = load_config()
    
    # 获取日期（从命令行参数或使用今天）
    if len(sys.argv) > 1:
        date = sys.argv[1]
    else:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"正在为日期 {date} 生成HTML...")
    
    # 获取日期文件夹路径
    base_dir = get_output_base_dir(config)
    date_folder = base_dir / date
    
    # 检查文件夹是否存在
    if not date_folder.exists():
        print(f"错误: 日期文件夹不存在: {date_folder}")
        sys.exit(1)
    
    # 读取所有Markdown文件
    articles = read_markdown_files_from_folder(date_folder)
    
    if not articles:
        print(f"错误: 日期文件夹中没有找到可用的Markdown文件: {date_folder}")
        sys.exit(1)
    
    print(f"找到 {len(articles)} 篇文章")
    
    # 生成邮件主题
    prefix = config.get("email", {}).get("default_subject_prefix", "NewsFlow")
    subject = f"{prefix} - {date} 新闻摘要"
    
    # 生成HTML邮件正文
    html_content = generate_email_html(articles, date)
    
    # 保存HTML文件
    html_file = date_folder / f"newsflow_{date}.html"
    html_file.write_text(html_content, encoding='utf-8')
    
    print(f"✓ HTML文件已生成: {html_file}")
    print(f"  共 {len(articles)} 篇文章")
    print(f"  主题: {subject}")
    print(f"\n文件路径: {html_file.absolute()}")

if __name__ == "__main__":
    main()

