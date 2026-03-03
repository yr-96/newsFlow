"""
HTML RAG 检索模块
提供基于RAG架构的HTML文本检索功能
"""
# 延迟导入，避免在模块加载时就需要numpy
__all__ = ['retrieve_relevant_chunks']

def retrieve_relevant_chunks(*args, **kwargs):
    """延迟导入retrieve_relevant_chunks函数"""
    from .retriever import retrieve_relevant_chunks as _retrieve_relevant_chunks
    return _retrieve_relevant_chunks(*args, **kwargs)





