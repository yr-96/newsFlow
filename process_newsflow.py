#!/usr/bin/env python3
"""NewsFlow处理脚本 - 筛选和处理新闻链接"""
import re
import sys
from typing import List, Set

# 定义需要排除的模式（非新闻链接）
EXCLUDE_PATTERNS = [
    r'news\.ycombinator\.com/(news|newest|front|newcomments|ask|show|jobs|submit|login|vote|hide|from|item|lists|security|newsguidelines|newsfaq)',
    r'hn\.algolia\.com',
    r'ycombinator\.com/(apply|legal)',
    r'tldr\.tech/(newsletters|api|tech|ai|dev|design|infosec|devops|marketing|founders|crypto|data|fintech|privacy|product)/?$',
    r'tldr\.tech/\d{4}-\d{2}-\d{2}/?$',
    r'advertise\.tldr\.tech',
    r'jobs\.ashbyhq\.com',
]

# 定义新闻网站和文章特征
NEWS_INDICATORS = [
    r'/blog/',
    r'/article/',
    r'/story/',
    r'/news/',
    r'/post/',
    r'/202[0-9]/',
    r'\.html',
    r'techcrunch\.com',
    r'theverge\.com',
    r'arstechnica\.com',
    r'ft\.com',
    r'newyorker\.com',
    r'latimes\.com',
    r'bloomberglaw\.com',
    r'abcnews\.go\.com',
    r'thenewstack\.io',
    r'blog\.',
    r'medium\.com',
    r'substack\.com/p/',
    r'androidheadlines\.com',
    r'interestingengineering\.com',
    r'cnbc\.com',
]

def is_news_link(url: str) -> bool:
    """判断是否为新闻链接"""
    # 排除非新闻链接
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    # 检查新闻特征
    for indicator in NEWS_INDICATORS:
        if re.search(indicator, url, re.IGNORECASE):
            return True
    
    # 对于外部网站且路径较深的链接，可能是新闻
    if not any(domain in url for domain in ['ycombinator.com', 'tldr.tech', 'hn.algolia.com']):
        parts = url.split('/')
        if len(parts) >= 5:  # 有足够的路径深度
            # 排除github项目主页和npm包页面
            if 'github.com' in url or 'npmjs.com/package' in url:
                return False
            return True
    
    return False

def filter_news_links(all_links: List[str], max_per_site: int = None) -> List[str]:
    """筛选新闻链接"""
    news_links = []
    seen = set()
    
    for link in all_links:
        # 清理URL（移除UTM参数）
        clean_link = re.sub(r'[?&]utm_source=[^&]*', '', link)
        clean_link = clean_link.rstrip('&?')
        
        if clean_link not in seen and is_news_link(clean_link):
            news_links.append(clean_link)
            seen.add(clean_link)
    
    # 如果有限制，只返回前N个
    if max_per_site and len(news_links) > max_per_site:
        return news_links[:max_per_site]
    
    return news_links

if __name__ == '__main__':
    # 测试
    test_links = [
        'https://daymare.net/blogs/artificial-life/',
        'https://blog.cloudflare.com/20-percent-internet-upgrade/',
        'https://www.ft.com/content/91002071-7874-4cb7-9245-08ca0571c408',
        'https://news.ycombinator.com/newest',
        'https://techcrunch.com/2025/10/30/canva-launches-its-own-design-model-adds-new-ai-features-to-the-platform/',
    ]
    
    filtered = filter_news_links(test_links)
    print(f'筛选结果: {len(filtered)}/{len(test_links)}')
    for link in filtered:
        print(f'  ✓ {link}')

