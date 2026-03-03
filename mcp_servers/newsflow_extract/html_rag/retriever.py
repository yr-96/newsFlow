"""
检索逻辑模块
整合HTML解析、分块、向量化、检索和结果合并
"""
import time
from typing import Dict, List, Optional, Any
from .html_parser import parse_and_clean_html
from .chunker import Chunker
from .embedder import embed_texts, embed_query
from .vector_store import VectorStore


def retrieve_relevant_chunks(
    html_text: str,
    query: str,
    top_k: Optional[int] = None,
    min_similarity: Optional[float] = None,
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    从HTML文本中检索与查询最相关的文本块
    
    参数:
        html_text: HTML文本内容
        query: 查询问题
        top_k: 返回最相关的K个chunks（可选，从config读取）
        min_similarity: 最小相似度阈值（可选，从config读取）
        config: 配置字典（包含embedding、chunking、retrieval配置）
    
    返回:
        {
            "success": bool,
            "query": str,
            "results": List[Dict],
            "total_chunks": int,
            "retrieval_time": float,
            "error": str (如果失败)
        }
    """
    start_time = time.time()
    
    try:
        # 解析配置
        config = config or {}
        embedding_config = config.get('embedding', {})
        chunking_config = config.get('chunking', {})
        retrieval_config = config.get('retrieval', {})
        
        # 获取检索参数（优先级：参数 > config > 默认值）
        final_top_k = top_k or retrieval_config.get('default_top_k', 3)
        final_min_similarity = min_similarity if min_similarity is not None else retrieval_config.get('default_min_similarity', 0.3)
        merge_results = retrieval_config.get('merge_results', True)
        
        # 步骤1：HTML解析与清理
        parse_result = parse_and_clean_html(html_text)
        if not parse_result['success']:
            return {
                "success": False,
                "query": query,
                "results": [],
                "total_chunks": 0,
                "retrieval_time": time.time() - start_time,
                "error": parse_result.get('error', 'HTML解析失败'),
                "error_type": "HTML_PARSE_FAILED"
            }
        
        cleaned_text = parse_result['text']
        structure = parse_result.get('structure', [])
        
        if not cleaned_text or len(cleaned_text.strip()) == 0:
            return {
                "success": False,
                "query": query,
                "results": [],
                "total_chunks": 0,
                "retrieval_time": time.time() - start_time,
                "error": "HTML解析后没有提取到文本内容",
                "error_type": "HTML_PARSE_FAILED"
            }
        
        # 步骤2：文本分块
        chunker = Chunker(chunking_config)
        chunks = chunker.chunk_text(cleaned_text, structure)
        
        if not chunks:
            return {
                "success": False,
                "query": query,
                "results": [],
                "total_chunks": 0,
                "retrieval_time": time.time() - start_time,
                "error": "文本分块后没有生成任何chunks",
                "error_type": "CHUNKING_FAILED"
            }
        
        # 步骤3：向量化chunks
        try:
            chunk_texts = [chunk['text'] for chunk in chunks]
            chunk_vectors = embed_texts(chunk_texts, embedding_config)
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "results": [],
                "total_chunks": len(chunks),
                "retrieval_time": time.time() - start_time,
                "error": f"向量化失败: {str(e)}",
                "error_type": "EMBEDDING_FAILED"
            }
        
        # 步骤4：构建向量存储
        vector_store = VectorStore()
        vector_store.add_vectors(chunk_vectors, chunks)
        
        # 步骤5：向量化查询
        try:
            query_vector = embed_query(query, embedding_config)
            if query_vector.ndim > 1:
                query_vector = query_vector[0]  # 取第一个（也是唯一一个）
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "results": [],
                "total_chunks": len(chunks),
                "retrieval_time": time.time() - start_time,
                "error": f"查询向量化失败: {str(e)}",
                "error_type": "EMBEDDING_FAILED"
            }
        
        # 步骤6：检索
        results = vector_store.search(query_vector, top_k=final_top_k, min_similarity=final_min_similarity)
        
        # 步骤7：结果合并（如果启用）
        if merge_results and len(results) > 1:
            results = _merge_adjacent_chunks(results, chunks)
        
        retrieval_time = time.time() - start_time
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_chunks": len(chunks),
            "retrieval_time": retrieval_time,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "results": [],
            "total_chunks": 0,
            "retrieval_time": time.time() - start_time,
            "error": f"检索过程出错: {str(e)}",
            "error_type": "RETRIEVAL_FAILED"
        }


def _merge_adjacent_chunks(results: List[Dict], all_chunks: List[Dict]) -> List[Dict]:
    """
    合并相邻的相关chunks
    
    参数:
        results: 检索结果列表
        all_chunks: 所有chunks列表
    
    返回:
        合并后的结果列表
    """
    if not results:
        return results
    
    # 按position排序
    sorted_results = sorted(results, key=lambda x: x.get('position', 0))
    
    merged_results = []
    current_group = [sorted_results[0]]
    
    for i in range(1, len(sorted_results)):
        current_chunk = sorted_results[i]
        last_chunk = current_group[-1]
        
        # 检查是否相邻（position相差1或2）
        current_pos = current_chunk.get('position', 0)
        last_pos = last_chunk.get('position', 0)
        
        if current_pos - last_pos <= 2:
            # 相邻，合并
            current_group.append(current_chunk)
        else:
            # 不相邻，保存当前组，开始新组
            merged_results.append(_merge_chunk_group(current_group))
            current_group = [current_chunk]
    
    # 保存最后一组
    if current_group:
        merged_results.append(_merge_chunk_group(current_group))
    
    return merged_results


def _merge_chunk_group(chunk_group: List[Dict]) -> Dict:
    """合并一组chunks"""
    if len(chunk_group) == 1:
        return chunk_group[0]
    
    # 合并文本
    merged_text = '\n\n'.join([chunk['text'] for chunk in chunk_group])
    
    # 使用第一个chunk的元数据，更新文本和相似度
    merged_chunk = chunk_group[0].copy()
    merged_chunk['text'] = merged_text
    merged_chunk['similarity'] = max([chunk['similarity'] for chunk in chunk_group])  # 使用最高相似度
    merged_chunk['merged_count'] = len(chunk_group)  # 记录合并的chunk数量
    
    return merged_chunk





