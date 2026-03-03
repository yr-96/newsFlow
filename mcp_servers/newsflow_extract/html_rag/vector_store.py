"""
内存向量存储模块
使用numpy数组存储向量，支持快速相似度检索
"""
from typing import List, Dict, Optional
import numpy as np


class VectorStore:
    """内存向量存储"""
    
    def __init__(self):
        """初始化向量存储"""
        self.vectors = None  # numpy数组，形状为 (n_chunks, embedding_dim)
        self.metadata = []  # chunk元数据列表
        self.chunk_to_index = {}  # chunk_id到索引的映射
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict]):
        """
        添加向量和元数据
        
        参数:
            vectors: 向量数组，形状为 (n_chunks, embedding_dim)
            metadata: 元数据列表，长度应与vectors的第一维相同
        """
        if len(vectors) != len(metadata):
            raise ValueError(f"向量数量({len(vectors)})与元数据数量({len(metadata)})不匹配")
        
        self.vectors = vectors
        self.metadata = metadata
        self.chunk_to_index = {
            chunk['chunk_id']: i for i, chunk in enumerate(metadata)
        }
    
    def search(self, query_vector: np.ndarray, top_k: int = 3, min_similarity: float = 0.3) -> List[Dict]:
        """
        搜索最相似的chunks
        
        参数:
            query_vector: 查询向量，形状为 (embedding_dim,)
            top_k: 返回最相似的K个chunks
            min_similarity: 最小相似度阈值
        
        返回:
            List[Dict]: 最相似的chunks列表，每个包含：
                {
                    "chunk_id": str,
                    "text": str,
                    "similarity": float,
                    "html_tag": str,
                    "position": int,
                    ...
                }
        """
        if self.vectors is None or len(self.vectors) == 0:
            return []
        
        # 确保query_vector是1维数组
        if query_vector.ndim > 1:
            query_vector = query_vector.flatten()
        
        # 计算余弦相似度（向量已归一化，直接计算内积）
        similarities = np.dot(self.vectors, query_vector)
        
        # 获取Top-K索引
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # 构建结果
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            
            # 过滤低于阈值的
            if similarity < min_similarity:
                continue
            
            chunk_data = self.metadata[idx].copy()
            chunk_data['similarity'] = similarity
            results.append(chunk_data)
        
        return results
    
    def clear(self):
        """清空向量存储"""
        self.vectors = None
        self.metadata = []
        self.chunk_to_index = {}
    
    def size(self) -> int:
        """返回存储的chunk数量"""
        return len(self.metadata) if self.metadata else 0





