"""
向量化模块
使用sentence-transformers将文本转化为向量
支持懒加载模型（首次调用时加载）
"""
import sys
from typing import List, Optional, Dict
import numpy as np

# 全局模型实例（懒加载）
_embedding_model = None
_model_config = None


def get_embedding_model(config: Optional[Dict] = None):
    """
    获取embedding模型（懒加载）
    
    参数:
        config: 模型配置
    
    返回:
        SentenceTransformer模型实例
    """
    global _embedding_model, _model_config
    
    # 如果模型已加载且配置相同，直接返回
    if _embedding_model is not None:
        # 检查配置是否变化
        if config and config != _model_config:
            # 配置变化，重新加载
            _embedding_model = None
    
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            
            model_config = config or {}
            model_name = model_config.get('model_name', 'paraphrase-multilingual-mpnet-base-v2')
            device = model_config.get('device', 'cpu')
            
            # 显示加载进度
            print(f"正在加载embedding模型: {model_name}...", file=sys.stderr)
            print(f"这可能需要几分钟时间（首次下载）...", file=sys.stderr)
            
            # 加载模型（首次会下载）
            _embedding_model = SentenceTransformer(model_name, device=device)
            _model_config = model_config.copy()
            
            print(f"✅ 模型加载成功", file=sys.stderr)
            
        except ImportError:
            raise ImportError(
                "sentence-transformers未安装。请运行: pip install sentence-transformers"
            )
        except Exception as e:
            raise RuntimeError(f"模型加载失败: {str(e)}")
    
    return _embedding_model


def embed_texts(texts: List[str], config: Optional[Dict] = None) -> np.ndarray:
    """
    将文本列表转化为向量
    
    参数:
        texts: 文本列表
        config: 模型配置
    
    返回:
        numpy数组，形状为 (len(texts), embedding_dim)
    """
    if not texts:
        return np.array([])
    
    model = get_embedding_model(config)
    
    model_config = config or {}
    batch_size = model_config.get('batch_size', 32)
    normalize = model_config.get('normalize_embeddings', True)
    
    # 批量向量化
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=normalize,
        convert_to_numpy=True
    )
    
    return embeddings


def embed_query(query: str, config: Optional[Dict] = None) -> np.ndarray:
    """
    将查询问题转化为向量
    
    参数:
        query: 查询文本
        config: 模型配置
    
    返回:
        numpy数组，形状为 (1, embedding_dim)
    """
    return embed_texts([query], config)





