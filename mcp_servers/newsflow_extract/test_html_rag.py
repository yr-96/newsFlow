"""
HTML RAG检索工具测试用例
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.newsflow_extract.html_rag.retriever import retrieve_relevant_chunks


def test_html_rag():
    """测试HTML RAG检索功能"""
    
    # 测试HTML内容（包含中英文）
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
                <section>
                    <h2>深度学习</h2>
                    <p>深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的工作方式。</p>
                    <p>深度学习在图像识别、语音识别、自然语言处理等领域表现出色。</p>
                </section>
            </article>
            <article>
                <h1>Web Development</h1>
                <p>Web development involves creating websites and web applications using various technologies.</p>
                <p>Frontend technologies include HTML, CSS, and JavaScript, while backend technologies include Python, Node.js, and Java.</p>
            </article>
        </main>
        <footer>
            <p>版权所有 © 2025</p>
        </footer>
    </body>
    </html>
    """
    
    print("=" * 60)
    print("🧪 HTML RAG 检索工具测试")
    print("=" * 60)
    print()
    
    # 测试用例1：中文查询
    print("测试用例1：中文查询 - '什么是机器学习？'")
    print("-" * 60)
    result1 = retrieve_relevant_chunks(
        html_text=html_content,
        query="什么是机器学习？",
        top_k=3,
        min_similarity=0.3
    )
    print(f"✅ 成功: {result1.get('success')}")
    print(f"📊 总chunks数: {result1.get('total_chunks')}")
    print(f"🔍 检索到结果数: {len(result1.get('results', []))}")
    print(f"⏱️  检索时间: {result1.get('retrieval_time', 0):.3f}秒")
    if result1.get('success'):
        print("\n检索结果:")
        for i, res in enumerate(result1.get('results', [])[:3], 1):
            print(f"\n结果 {i}:")
            print(f"  相似度: {res.get('similarity', 0):.3f}")
            print(f"  文本: {res.get('text', '')[:200]}...")
    else:
        print(f"❌ 错误: {result1.get('error')}")
    print()
    
    # 测试用例2：英文查询
    print("测试用例2：英文查询 - 'What is web development?'")
    print("-" * 60)
    result2 = retrieve_relevant_chunks(
        html_text=html_content,
        query="What is web development?",
        top_k=2,
        min_similarity=0.3
    )
    print(f"✅ 成功: {result2.get('success')}")
    print(f"📊 总chunks数: {result2.get('total_chunks')}")
    print(f"🔍 检索到结果数: {len(result2.get('results', []))}")
    print(f"⏱️  检索时间: {result2.get('retrieval_time', 0):.3f}秒")
    if result2.get('success'):
        print("\n检索结果:")
        for i, res in enumerate(result2.get('results', [])[:2], 1):
            print(f"\n结果 {i}:")
            print(f"  相似度: {res.get('similarity', 0):.3f}")
            print(f"  文本: {res.get('text', '')[:200]}...")
    else:
        print(f"❌ 错误: {result2.get('error')}")
    print()
    
    # 测试用例3：深度学习查询
    print("测试用例3：查询 - '深度学习的特点'")
    print("-" * 60)
    result3 = retrieve_relevant_chunks(
        html_text=html_content,
        query="深度学习的特点",
        top_k=2
    )
    print(f"✅ 成功: {result3.get('success')}")
    print(f"📊 总chunks数: {result3.get('total_chunks')}")
    print(f"🔍 检索到结果数: {len(result3.get('results', []))}")
    print(f"⏱️  检索时间: {result3.get('retrieval_time', 0):.3f}秒")
    if result3.get('success'):
        print("\n检索结果:")
        for i, res in enumerate(result3.get('results', [])[:2], 1):
            print(f"\n结果 {i}:")
            print(f"  相似度: {res.get('similarity', 0):.3f}")
            print(f"  文本: {res.get('text', '')[:200]}...")
    else:
        print(f"❌ 错误: {result3.get('error')}")
    print()
    
    # 测试用例4：使用配置
    print("测试用例4：使用配置文件中的参数")
    print("-" * 60)
    config = {
        'embedding': {
            'model_name': 'paraphrase-multilingual-mpnet-base-v2',
            'device': 'cpu',
            'batch_size': 32,
            'normalize_embeddings': True
        },
        'chunking': {
            'min_chunk_size': 100,
            'max_chunk_size': 1000,
            'chunk_overlap': 50,
            'prefer_semantic': True,
            'fallback_to_paragraph': True
        },
        'retrieval': {
            'default_top_k': 3,
            'default_min_similarity': 0.3,
            'merge_results': True
        }
    }
    result4 = retrieve_relevant_chunks(
        html_text=html_content,
        query="人工智能的应用领域",
        config=config
    )
    print(f"✅ 成功: {result4.get('success')}")
    print(f"📊 总chunks数: {result4.get('total_chunks')}")
    print(f"🔍 检索到结果数: {len(result4.get('results', []))}")
    print(f"⏱️  检索时间: {result4.get('retrieval_time', 0):.3f}秒")
    if result4.get('success'):
        print("\n检索结果:")
        for i, res in enumerate(result4.get('results', [])[:3], 1):
            print(f"\n结果 {i}:")
            print(f"  相似度: {res.get('similarity', 0):.3f}")
            print(f"  文本: {res.get('text', '')[:200]}...")
    else:
        print(f"❌ 错误: {result4.get('error')}")
    print()
    
    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    
    # 返回测试结果摘要
    return {
        "test1_success": result1.get('success'),
        "test2_success": result2.get('success'),
        "test3_success": result3.get('success'),
        "test4_success": result4.get('success')
    }


if __name__ == "__main__":
    try:
        results = test_html_rag()
        # 检查是否有失败的测试
        if all([results['test1_success'], results['test2_success'], 
                results['test3_success'], results['test4_success']]):
            print("\n🎉 所有测试通过！")
            sys.exit(0)
        else:
            print("\n⚠️  部分测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)





