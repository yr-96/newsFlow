"""
fetch_html_from_url 工具测试
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.newsflow_extract.fetcher import fetch_html_from_url


def test_fetch_html():
    """测试获取 HTML"""
    print("=" * 60)
    print("🧪 fetch_html_from_url 测试")
    print("=" * 60)

    # 测试一个简单的静态页面
    url = "https://example.com"
    result = fetch_html_from_url(url, timeout=10)

    print(f"URL: {url}")
    print(f"成功: {result.get('success')}")
    print(f"标题: {result.get('title', '')[:80]}...")
    print(f"HTML 长度: {len(result.get('html', ''))} 字符")

    if result.get("error"):
        print(f"错误: {result.get('error')}")

    if result.get("success"):
        html = result.get("html", "")
        assert "Example Domain" in html or "example.com" in html
        print("\n✅ 测试通过")
        return True
    else:
        print("\n⚠️ 测试失败（可能是网络问题）")
        return False


if __name__ == "__main__":
    try:
        ok = test_fetch_html()
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
