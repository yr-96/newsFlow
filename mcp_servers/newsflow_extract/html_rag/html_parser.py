"""
HTML解析与清理模块
从HTML中提取有意义的文本内容，去除噪音
"""
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Tag, NavigableString


def parse_and_clean_html(html_text: str) -> Dict[str, any]:
    """
    解析HTML并清理，提取有意义的文本内容
    
    参数:
        html_text: HTML文本内容
    
    返回:
        {
            "text": str,  # 清理后的文本
            "structure": List[Dict],  # 结构化信息（标题、段落等）
            "success": bool,  # 是否成功
            "error": str  # 错误信息（如果有）
        }
    """
    try:
        # 解析HTML
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # 移除噪音标签
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 
                                  'aside', 'meta', 'link', 'noscript']):
            tag.decompose()
        
        # 提取结构化信息
        structure = []
        text_parts = []
        
        # 优先提取语义标签
        semantic_tags = soup.find_all(['article', 'main', 'section'])
        if semantic_tags:
            for tag in semantic_tags:
                text = _extract_text_from_tag(tag)
                if text and len(text.strip()) > 0:
                    structure.append({
                        'type': tag.name,
                        'text': text,
                        'position': len(text_parts)
                    })
                    text_parts.append(text)
        else:
            # 如果没有语义标签，提取段落和标题
            for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'li']):
                text = _extract_text_from_tag(tag)
                if text and len(text.strip()) > 0:
                    structure.append({
                        'type': tag.name,
                        'text': text,
                        'position': len(text_parts)
                    })
                    text_parts.append(text)
        
        # 合并文本
        cleaned_text = '\n\n'.join(text_parts)
        
        # 规范化文本
        cleaned_text = _normalize_text(cleaned_text)
        
        return {
            "text": cleaned_text,
            "structure": structure,
            "success": True,
            "error": None
        }
        
    except Exception as e:
        # 部分解析：尝试提取所有文本
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            # 移除脚本和样式
            for tag in soup.find_all(['script', 'style']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)
            text = _normalize_text(text)
            return {
                "text": text,
                "structure": [],
                "success": True,  # 部分成功
                "error": f"部分解析成功，但可能丢失部分结构: {str(e)}"
            }
        except Exception as e2:
            return {
                "text": "",
                "structure": [],
                "success": False,
                "error": f"HTML解析失败: {str(e2)}"
            }


def _extract_text_from_tag(tag: Tag) -> str:
    """从标签中提取文本"""
    if isinstance(tag, NavigableString):
        return str(tag).strip()
    
    # 获取标签内的文本，但排除子标签
    texts = []
    for element in tag.children:
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if text:
                texts.append(text)
        elif isinstance(element, Tag):
            # 递归提取子标签文本
            sub_text = _extract_text_from_tag(element)
            if sub_text:
                texts.append(sub_text)
    
    return ' '.join(texts)


def _normalize_text(text: str) -> str:
    """规范化文本"""
    # 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 去除多余的空白字符（保留单个空格和换行）
    text = re.sub(r'[ \t]+', ' ', text)  # 多个空格/制表符变为单个空格
    text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行变为两个换行
    
    # 去除HTML实体
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    # 去除不可见字符（保留换行和空格）
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()





