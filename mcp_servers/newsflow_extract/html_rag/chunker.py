"""
文本分块模块
将HTML文本分割成语义完整、大小适中的文本块
"""
from typing import Dict, List, Optional
import re


class Chunker:
    """文本分块器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化分块器
        
        参数:
            config: 分块配置
        """
        self.config = config or {}
        self.min_chunk_size = self.config.get('min_chunk_size', 100)
        self.max_chunk_size = self.config.get('max_chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 50)
        self.prefer_semantic = self.config.get('prefer_semantic', True)
        self.fallback_to_paragraph = self.config.get('fallback_to_paragraph', True)
    
    def chunk_text(self, text: str, structure: List[Dict] = None) -> List[Dict]:
        """
        将文本分块
        
        参数:
            text: 要分块的文本
            structure: HTML结构信息（可选）
        
        返回:
            List[Dict]: chunk列表，每个chunk包含：
                {
                    "chunk_id": str,
                    "text": str,
                    "html_tag": str,
                    "position": int,
                    "char_count": int
                }
        """
        chunks = []
        
        # 策略1：基于HTML结构的语义分块（优先）
        if self.prefer_semantic and structure:
            chunks = self._semantic_chunking(text, structure)
            if chunks:
                return chunks
        
        # 策略2：基于段落的分块（兜底）
        if self.fallback_to_paragraph:
            chunks = self._paragraph_chunking(text)
            if chunks:
                return chunks
        
        # 策略3：固定大小分块（最后兜底）
        if not chunks:
            chunks = self._fixed_size_chunking(text)
        
        return chunks
    
    def _semantic_chunking(self, text: str, structure: List[Dict]) -> List[Dict]:
        """基于HTML结构的语义分块"""
        chunks = []
        chunk_id = 0
        
        for item in structure:
            chunk_text = item.get('text', '').strip()
            if not chunk_text:
                continue
            
            # 如果chunk太大，需要进一步分割
            if len(chunk_text) > self.max_chunk_size:
                sub_chunks = self._split_large_chunk(chunk_text)
                for sub_chunk in sub_chunks:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id:03d}",
                        "text": sub_chunk,
                        "html_tag": item.get('type', 'unknown'),
                        "position": item.get('position', chunk_id),
                        "char_count": len(sub_chunk)
                    })
                    chunk_id += 1
            elif len(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    "chunk_id": f"chunk_{chunk_id:03d}",
                    "text": chunk_text,
                    "html_tag": item.get('type', 'unknown'),
                    "position": item.get('position', chunk_id),
                    "char_count": len(chunk_text)
                })
                chunk_id += 1
            else:
                # 小chunk，尝试合并到前一个chunk
                if chunks and len(chunks[-1]['text']) + len(chunk_text) <= self.max_chunk_size:
                    chunks[-1]['text'] += '\n\n' + chunk_text
                    chunks[-1]['char_count'] = len(chunks[-1]['text'])
                else:
                    # 无法合并，单独成chunk（如果达到最小大小）
                    if len(chunk_text) >= self.min_chunk_size // 2:  # 降低最小大小要求
                        chunks.append({
                            "chunk_id": f"chunk_{chunk_id:03d}",
                            "text": chunk_text,
                            "html_tag": item.get('type', 'unknown'),
                            "position": item.get('position', chunk_id),
                            "char_count": len(chunk_text)
                        })
                        chunk_id += 1
        
        return chunks
    
    def _paragraph_chunking(self, text: str) -> List[Dict]:
        """基于段落的分块"""
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\n+', text)
        chunks = []
        chunk_id = 0
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前chunk加上新段落不超过最大大小，合并
            if current_chunk and len(current_chunk) + len(para) + 2 <= self.max_chunk_size:
                current_chunk += '\n\n' + para
            else:
                # 保存当前chunk
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id:03d}",
                        "text": current_chunk,
                        "html_tag": "paragraph",
                        "position": chunk_id,
                        "char_count": len(current_chunk)
                    })
                    chunk_id += 1
                
                # 开始新chunk
                if len(para) > self.max_chunk_size:
                    # 段落太大，需要分割
                    sub_chunks = self._split_large_chunk(para)
                    for sub_chunk in sub_chunks:
                        if len(sub_chunk) >= self.min_chunk_size:
                            chunks.append({
                                "chunk_id": f"chunk_{chunk_id:03d}",
                                "text": sub_chunk,
                                "html_tag": "paragraph",
                                "position": chunk_id,
                                "char_count": len(sub_chunk)
                            })
                            chunk_id += 1
                        else:
                            current_chunk = sub_chunk
                else:
                    current_chunk = para
        
        # 保存最后一个chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "chunk_id": f"chunk_{chunk_id:03d}",
                "text": current_chunk,
                "html_tag": "paragraph",
                "position": chunk_id,
                "char_count": len(current_chunk)
            })
        
        return chunks
    
    def _fixed_size_chunking(self, text: str) -> List[Dict]:
        """固定大小分块（最后兜底）"""
        chunks = []
        chunk_id = 0
        
        # 按句子分割（尝试保持语义）
        sentences = re.split(r'[.!?。！？]\s+', text)
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= self.max_chunk_size:
                current_chunk += ('. ' if current_chunk else '') + sentence
            else:
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id:03d}",
                        "text": current_chunk,
                        "html_tag": "text",
                        "position": chunk_id,
                        "char_count": len(current_chunk)
                    })
                    chunk_id += 1
                
                # 如果单个句子就超过最大大小，强制分割
                if len(sentence) > self.max_chunk_size:
                    sub_chunks = self._split_large_chunk(sentence)
                    for sub_chunk in sub_chunks:
                        if len(sub_chunk) >= self.min_chunk_size:
                            chunks.append({
                                "chunk_id": f"chunk_{chunk_id:03d}",
                                "text": sub_chunk,
                                "html_tag": "text",
                                "position": chunk_id,
                                "char_count": len(sub_chunk)
                            })
                            chunk_id += 1
                    current_chunk = ""
                else:
                    current_chunk = sentence
        
        # 保存最后一个chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                "chunk_id": f"chunk_{chunk_id:03d}",
                "text": current_chunk,
                "html_tag": "text",
                "position": chunk_id,
                "char_count": len(current_chunk)
            })
        
        return chunks
    
    def _split_large_chunk(self, text: str) -> List[str]:
        """分割过大的chunk"""
        chunks = []
        # 按句子分割
        sentences = re.split(r'[.!?。！？]\s+', text)
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= self.max_chunk_size:
                current_chunk += ('. ' if current_chunk else '') + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks





