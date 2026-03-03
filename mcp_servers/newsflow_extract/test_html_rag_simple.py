"""
HTML RAG检索工具简化测试用例（不依赖模型）
测试HTML解析和分块功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.newsflow_extract.html_rag.html_parser import parse_and_clean_html
from mcp_servers.newsflow_extract.html_rag.chunker import Chunker


def test_html_parser():
    """测试HTML解析功能"""
    print("=" * 60)
    print("🧪 HTML解析功能测试")
    print("=" * 60)
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>测试页面</title>
        <script>console.log('test');</script>
        <style>body { color: black; }</style>
    </head>
    <body>
        <header>
            <nav>导航栏</nav>
        </header>
        <main>
            <article>
                <h1>人工智能的发展</h1>
                <p>人工智能（Artificial Intelligence, AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。</p>
                <p>近年来，AI技术在机器学习、深度学习、自然语言处理等领域取得了重大突破。</p>
                <section>
                    <h2>机器学习</h2>
                    <p>机器学习是AI的核心技术之一，它使计算机能够从数据中学习，而无需明确编程。</p>
                    <p>常见的机器学习算法包括线性回归、决策树、神经网络等。</p>
                </section>
            </article>
        </main>
        <footer>
            <p>版权所有 © 2025</p>
        </footer>
    </body>
    </html>
    """
    
    result = parse_and_clean_html(html_content)
    
    print(f"✅ 解析成功: {result.get('success')}")
    if result.get('error'):
        print(f"⚠️  警告: {result.get('error')}")
    print(f"📝 提取文本长度: {len(result.get('text', ''))} 字符")
    print(f"📊 结构化信息数量: {len(result.get('structure', []))}")
    
    if result.get('success'):
        print("\n提取的文本（前500字符）:")
        print("-" * 60)
        print(result.get('text', '')[:500])
        print()
        
        print("结构化信息:")
        for i, item in enumerate(result.get('structure', [])[:5], 1):
            print(f"  {i}. {item.get('type')}: {item.get('text', '')[:100]}...")
    
    return result.get('success')


def test_chunker():
    """测试文本分块功能"""
    print("\n" + "=" * 60)
    print("🧪 文本分块功能测试")
    print("=" * 60)
    
    # 测试文本
    test_text = """
    人工智能（Artificial Intelligence, AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。
    
    近年来，AI技术在机器学习、深度学习、自然语言处理等领域取得了重大突破。
    
    机器学习是AI的核心技术之一，它使计算机能够从数据中学习，而无需明确编程。常见的机器学习算法包括线性回归、决策树、神经网络等。
    
    深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的工作方式。深度学习在图像识别、语音识别、自然语言处理等领域表现出色。
    
    Web development involves creating websites and web applications using various technologies. Frontend technologies include HTML, CSS, and JavaScript, while backend technologies include Python, Node.js, and Java.
    """
    
    structure = [
        {'type': 'article', 'text': test_text.strip(), 'position': 0}
    ]
    
    chunker = Chunker({
        'min_chunk_size': 100,
        'max_chunk_size': 500,
        'chunk_overlap': 50,
        'prefer_semantic': True,
        'fallback_to_paragraph': True
    })
    
    chunks = chunker.chunk_text(test_text, structure)
    
    print(f"✅ 分块成功")
    print(f"📊 生成chunks数量: {len(chunks)}")
    
    print("\nChunks详情:")
    for i, chunk in enumerate(chunks[:5], 1):
        print(f"\n  Chunk {i} ({chunk.get('chunk_id')}):")
        print(f"    大小: {chunk.get('char_count')} 字符")
        print(f"    标签: {chunk.get('html_tag')}")
        print(f"    位置: {chunk.get('position')}")
        print(f"    文本: {chunk.get('text', '')[:150]}...")
    
    return len(chunks) > 0


def test_full_pipeline_without_model():
    """测试完整流程（不包含向量化）"""
    print("\n" + "=" * 60)
    print("🧪 完整流程测试（不含向量化）")
    print("=" * 60)
    
    html_content = """
    <html>
    <body>
        <article>
            <h1>Python编程语言</h1>
            <p>Python是一种高级编程语言，以其简洁的语法和强大的功能而闻名。</p>
            <p>Python广泛应用于Web开发、数据科学、人工智能、自动化脚本等领域。</p>
            <section>
                <h2>特点</h2>
                <p>Python具有以下特点：易学易用、跨平台、丰富的库生态系统、强大的社区支持。</p>
            </section>
        </article>
    </body>
    </html>
    """
    
    # 步骤1：解析
    parse_result = parse_and_clean_html(html_content)
    if not parse_result.get('success'):
        print(f"❌ HTML解析失败: {parse_result.get('error')}")
        return False
    
    # 步骤2：分块
    chunker = Chunker()
    chunks = chunker.chunk_text(parse_result['text'], parse_result.get('structure'))
    
    print(f"✅ HTML解析成功")
    print(f"✅ 文本分块成功，生成 {len(chunks)} 个chunks")
    print(f"📝 提取文本长度: {len(parse_result['text'])} 字符")
    
    if chunks:
        print("\n生成的chunks:")
        for i, chunk in enumerate(chunks, 1):
            print(f"  {i}. {chunk.get('chunk_id')}: {chunk.get('text', '')[:100]}...")
    
    return True


if __name__ == "__main__":
    try:
        print("\n开始测试HTML RAG模块（不含向量化部分）...\n")
        
        # 测试1：HTML解析
        test1_ok = test_html_parser()
        
        # 测试2：文本分块
        test2_ok = test_chunker()
        
        # 测试3：完整流程（不含向量化）
        test3_ok = test_full_pipeline_without_model()
        
        print("\n" + "=" * 60)
        if test1_ok and test2_ok and test3_ok:
            print("✅ 所有测试通过！")
            print("\n注意：向量化功能需要安装 sentence-transformers")
            print("运行以下命令安装依赖：")
            print("  pip install sentence-transformers numpy")
            sys.exit(0)
        else:
            print("⚠️  部分测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)





