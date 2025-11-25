#!/usr/bin/env python3
"""
NewsFlow 自动化处理脚本
从配置的新闻网站提取最新文章，生成总结并发送邮件
"""
import yaml
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
import json

# 添加MCP服务器路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "mcp_servers" / "newsflow_extract"))
sys.path.insert(0, str(project_root / "mcp_servers" / "newsflow_writer"))

from process_newsflow import filter_news_links

def load_config():
    """加载配置文件"""
    config_path = project_root / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def extract_news_links_from_site(url: str, site_name: str) -> List[str]:
    """从网站提取新闻链接（需要调用MCP工具，这里返回示例）"""
    # 实际应该调用MCP工具 extract_links_from_url
    # 这里返回示例结构
    print(f"  [提取] {site_name}: {url}")
    # TODO: 调用MCP工具
    return []

def main():
    """主函数"""
    print("=" * 60)
    print("开始执行 NewsFlow 流程...")
    print("=" * 60)
    
    # 第一步：读取配置文件
    print("\n[步骤1] 读取配置文件 config.yaml")
    config = load_config()
    websites = [site for site in config.get('websites', []) if site.get('enabled', False)]
    email_config = config.get('email', {})
    settings = config.get('settings', {})
    max_articles = settings.get('max_articles_per_site', 10)
    
    print(f"  - 找到 {len(websites)} 个启用的网站")
    
    # 第二步：提取新闻链接
    print("\n[步骤2] 提取新闻链接")
    all_news_links = []
    for site in websites:
        site_name = site.get('name', 'Unknown')
        site_url = site.get('url', '')
        print(f"  - {site_name}: {site_url}")
        # 实际应该调用MCP工具
        # links = extract_news_links_from_site(site_url, site_name)
        # filtered = filter_news_links(links, max_articles)
        # all_news_links.extend(filtered)
    
    # 去重
    unique_links = list(set(all_news_links))
    print(f"  - 总计: {len(unique_links)} 个新闻链接（已去重）")
    
    # 第三步：处理新闻链接
    print("\n[步骤3] 处理新闻链接")
    print(f"  - 正在处理 {len(unique_links)} 个链接...")
    # TODO: 处理每个链接
    
    # 第四步：发送邮件
    print("\n[步骤4] 发送邮件")
    today = datetime.now().strftime('%Y-%m-%d')
    recipient_emails = email_config.get('recipient_emails', [])
    print(f"  - 读取今天日期文件夹: output/{today}")
    print(f"  - 邮件将发送到: {', '.join(recipient_emails)}")
    # TODO: 调用MCP工具发送邮件
    
    # 第五步：总结报告
    print("\n[完成] NewsFlow 流程执行完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()

