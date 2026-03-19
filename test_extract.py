#!/usr/bin/env python3
"""测试 extract_links_from_url"""
import json
from mcp_servers.newsflow_extract.extractor import extract_links_from_url

if __name__ == "__main__":
    url = "https://news.ycombinator.com/newest"  # 改成你要测试的 URL
    result = extract_links_from_url(url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
