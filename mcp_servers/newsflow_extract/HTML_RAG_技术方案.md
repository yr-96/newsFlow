# HTML RAG 检索工具技术方案

## 📋 项目概述

### 功能描述

实现一个基于RAG（Retrieval-Augmented Generation）架构的HTML文本检索工具，能够：
1. 接收HTML结构的文本和一个查询问题
2. 将问题转化为向量表示
3. 将HTML文本进行智能分块，并转化为向量
4. 通过向量相似度检索，返回与问题最相关的文本块

### 应用场景

- 从网页HTML中提取特定信息
- 回答关于网页内容的问题
- 快速定位HTML中的关键内容
- 支持多语言新闻文章、技术文档等结构化内容的检索
- **多语言支持**：支持50+语言的HTML内容检索

## 🏗️ 系统架构

```
输入层
  ├── HTML文本（结构化内容，支持多语言）
  └── 查询问题（自然语言，支持多语言）

处理层
  ├── HTML解析与清理（多语言文本处理）
  ├── 文本分块（Chunking）
  ├── 向量化（Embedding - 多语言模型）
  └── 向量存储（Vector Store）

检索层
  ├── 查询向量化（多语言查询）
  ├── 相似度计算
  ├── Top-K检索
  └── 结果排序

输出层
  └── 最相关的文本块（Top-K结果，支持多语言）
```

## 🔧 技术方案设计

### 1. HTML解析与预处理

#### 1.1 HTML清理策略

**目标**：提取有意义的文本内容，去除噪音，支持多语言

**实现步骤**：
1. **使用BeautifulSoup解析HTML**
   - 保留主要语义标签：`<article>`, `<main>`, `<section>`, `<div>`, `<p>`, `<h1-h6>`, `<li>`, `<td>`, `<th>`
   - 移除噪音标签：`<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<aside>`, `<meta>`, `<link>`

2. **文本提取与清理**
   - 提取纯文本内容（支持多语言字符）
   - 去除多余的空白字符（保留单个空格）
   - 去除特殊字符和不可见字符
   - 保留换行符用于段落识别
   - **多语言处理**：保留Unicode字符，支持中文、日文、韩文、阿拉伯文等

3. **结构化信息保留**
   - 保留标题层级（h1-h6）用于分块
   - 保留列表结构
   - 保留表格结构（可选）

#### 1.2 文本规范化

- 统一编码（UTF-8）
- 统一换行符（\n）
- 去除HTML实体（如 `&nbsp;`, `&amp;` 等）
- **多语言文本处理**：支持中英文、日文、韩文、法文、德文、西班牙文、俄文、阿拉伯文等50+语言

### 2. 文本分块策略（Chunking）

#### 2.1 分块原则

**目标**：将HTML文本分割成语义完整、大小适中的文本块

**分块策略（优先级顺序）**：

1. **基于HTML结构的语义分块**（主要策略）
   - 按 `<article>`, `<section>`, `<div class="content">` 等语义标签分割
   - 每个语义块作为一个chunk
   - 优点：保持语义完整性，适合多语言内容

2. **基于标题层级的分块**（辅助策略）
   - 识别 `<h1>`, `<h2>`, `<h3>` 等标题（支持多语言标题）
   - 将标题及其后续内容作为一个chunk
   - 直到遇到同级或更高级标题为止

3. **基于段落的分块**（兜底策略）
   - 按 `<p>` 标签或连续文本段落分割
   - 合并相邻小段落，避免chunk过小
   - 支持多语言段落识别

#### 2.2 分块参数配置

```python
CHUNK_CONFIG = {
    "min_chunk_size": 100,      # 最小chunk字符数（避免过小）
    "max_chunk_size": 1000,     # 最大chunk字符数（避免过大）
    "chunk_overlap": 50,        # chunk之间的重叠字符数（保持上下文）
    "prefer_semantic": True,     # 优先使用语义分块
    "fallback_to_paragraph": True  # 如果语义分块失败，使用段落分块
}
```

#### 2.3 分块元数据

每个chunk需要保存的元数据：
- `chunk_id`: 唯一标识符
- `text`: 文本内容（多语言）
- `html_tag`: 来源的HTML标签（如 `<article>`, `<section>`）
- `position`: 在原HTML中的位置（行号或索引）
- `parent_context`: 父级上下文（如所属的section标题）
- `char_count`: 字符数
- `language`: 检测到的语言（可选）

### 3. 向量化（Embedding）

#### 3.1 Embedding模型选择

**🎯 推荐方案：使用sentence-transformers + 多语言模型**

**最终推荐模型**：`paraphrase-multilingual-mpnet-base-v2`

**模型特点**：
- ✅ **支持50+语言**：包括中文、英文、日文、韩文、法文、德文、西班牙文、俄文、阿拉伯文、意大利文、葡萄牙文、荷兰文、波兰文、土耳其文、越南文、泰文、印尼文等
- ✅ **高质量**：基于mpnet架构，在语义搜索和文本相似度任务上表现优秀
- ✅ **向量维度**：768维，质量好
- ✅ **模型大小**：约1.2GB（适中）
- ✅ **官方维护**：sentence-transformers团队维护，稳定可靠
- ✅ **开源免费**：无需API key，本地运行

**模型使用说明**：
- `sentence-transformers` 库提供统一的接口
- 模型存储在 **Hugging Face Hub** 上，首次使用时自动下载
- 使用方式：`SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')`
- 模型下载后会缓存在本地 `~/.cache/huggingface/` 目录

**备选模型**（根据需求选择）：

1. **速度优先**：`paraphrase-multilingual-MiniLM-L12-v2`
   - 支持50+语言
   - 模型大小：420MB（更小）
   - 向量维度：384（更快）
   - 速度更快，但质量略低

2. **更多语言支持**：`intfloat/multilingual-e5-large`
   - 支持100+语言
   - 模型大小：约2.4GB（更大）
   - 向量维度：1024（更高）
   - 质量很高，但模型更大

#### 3.2 向量化实现

**流程**：
1. 初始化embedding模型（启动时加载一次）
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
   ```

2. 对每个chunk的文本进行向量化（支持多语言）
   ```python
   # 批量处理，支持多语言文本
   embeddings = model.encode(chunks, batch_size=32, show_progress_bar=True)
   ```

3. 对查询问题进行向量化（支持多语言查询）
   ```python
   query_embedding = model.encode([query])
   ```

4. 向量归一化（L2归一化，用于余弦相似度计算）
   ```python
   import numpy as np
   embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
   ```

**性能优化**：
- 批量处理chunks（batch processing，默认batch_size=32）
- 缓存已向量化的chunks（避免重复计算）
- 使用GPU加速（如果可用）：`model = SentenceTransformer('model-name', device='cuda')`

### 4. 向量存储（Vector Store）

#### 4.1 存储方案选择

**✅ 确定方案：内存存储**

**选择原因**：
- HTML文本去除噪音后文本量不会太大
- 每次调用HTML都不一样，不需要缓存
- 任务量小，内存存储足够
- 简单快速，无需额外依赖

**实现**：
- 使用numpy数组存储向量
- 使用Python列表存储元数据
- 每次调用重新构建，不缓存

#### 4.2 向量存储结构

```python
vector_store = {
    "vectors": np.ndarray,      # numpy数组，形状为 (n_chunks, embedding_dim)
    "metadata": [
        {
            "chunk_id": str,
            "text": str,         # 多语言文本
            "html_tag": str,
            "position": int,
            "parent_context": str,
            "language": str      # 可选：检测到的语言
        }
    ],
    "chunk_to_index": {chunk_id: index}  # chunk_id到向量索引的映射
}
```

### 5. 相似度检索

#### 5.1 相似度计算方法

**余弦相似度（推荐）**：
- 公式：`cos(θ) = (A · B) / (||A|| * ||B||)`
- 范围：[-1, 1]，值越大越相似
- 优点：不受向量长度影响，适合文本相似度，支持多语言

**实现**：
- 向量需要L2归一化
- 使用内积计算（归一化后的向量内积 = 余弦相似度）
- 实现使用 numpy 的 `np.dot` 进行内积计算，无需 FAISS

#### 5.2 Top-K检索策略

**流程**：
1. 将查询问题向量化（支持多语言查询）
2. 计算查询向量与所有chunk向量的相似度
3. 按相似度降序排序
4. 返回Top-K个最相关的chunks

**参数配置**：
```python
RETRIEVAL_CONFIG = {
    "top_k": 3,              # 返回最相关的K个chunks
    "min_similarity": 0.3,   # 最小相似度阈值（过滤低质量结果）
    "rerank": False          # 是否使用重排序（可选，提高精度）
}
```

#### 5.3 结果重排序（可选优化）

**目的**：提高检索精度

**方法**：
- 使用更复杂的模型（如cross-encoder）对Top-K结果重排序
- 考虑chunk的位置信息（前面的内容可能更重要）
- 考虑chunk的长度（适中长度的chunk可能更相关）

### 6. 结果返回

#### 6.1 返回格式

```python
{
    "query": str,                    # 原始查询问题（多语言）
    "results": [
        {
            "chunk_id": str,
            "text": str,             # chunk文本内容（多语言）
            "similarity": float,     # 相似度分数（0-1）
            "html_tag": str,         # 来源HTML标签
            "position": int,         # 在原HTML中的位置
            "parent_context": str    # 父级上下文
        }
    ],
    "total_chunks": int,            # 总chunk数量
    "retrieval_time": float         # 检索耗时（秒）
}
```

#### 6.2 结果优化

- ✅ **结果合并**：如果相邻chunks都相关，合并返回（必需功能）
- ❌ **去重**：不需要（由结果合并处理）
- ❌ **上下文补充**：不需要

## 📦 技术选型

### 核心依赖

```python
# HTML解析
beautifulsoup4>=4.12.0

# 向量化模型（多语言支持）
sentence-transformers>=2.2.0
# 注意：sentence-transformers会自动安装torch和transformers作为依赖

# 向量计算
numpy>=1.24.0

# 注意：不使用向量数据库，使用内存存储（numpy数组）
```

### 配置项（config.yaml）

```yaml
# HTML RAG配置
html_rag:
  # Embedding模型配置
  embedding:
    model_name: "paraphrase-multilingual-mpnet-base-v2"  # 模型名称
    device: "cpu"  # "cpu" 或 "cuda"（如果支持GPU）
    batch_size: 32  # 批量处理大小
    normalize_embeddings: true  # L2归一化
  
  # 分块配置
  chunking:
    min_chunk_size: 100  # 最小chunk字符数
    max_chunk_size: 1000  # 最大chunk字符数
    chunk_overlap: 50  # chunk重叠字符数
    prefer_semantic: true  # 优先使用语义分块
    fallback_to_paragraph: true  # 语义分块失败时使用段落分块
  
  # 检索配置
  retrieval:
    default_top_k: 3  # 默认返回的chunk数量
    default_min_similarity: 0.3  # 默认最小相似度阈值
    merge_results: true  # 是否合并相邻相关chunks
```

**配置优先级**：
- 接口参数 > config.yaml配置 > 默认值
- 例如：如果接口传入了top_k，使用接口参数；否则使用config.yaml中的default_top_k；都没有则使用默认值3

### 可选依赖

```python
# 如果使用OpenAI Embedding（不推荐，需要API key）
openai>=1.0.0

# 文本处理（可选）
nltk>=3.8  # 用于文本预处理
langdetect>=2.0  # 用于语言检测（可选）
```

## 🔄 实现流程

### 完整流程

```
1. 初始化阶段
   ├── 加载embedding模型（paraphrase-multilingual-mpnet-base-v2）
   ├── 初始化向量存储（numpy 内存存储）
   └── 加载配置参数

2. HTML处理阶段
   ├── 解析HTML（BeautifulSoup）
   ├── 清理和提取文本（支持多语言）
   └── 文本规范化（UTF-8编码）

3. 分块阶段
   ├── 识别HTML语义结构
   ├── 按策略分块（支持多语言文本）
   └── 生成chunk元数据

4. 向量化阶段
   ├── 批量向量化chunks（支持多语言）
   ├── 向量归一化（L2归一化）
   └── 存储到向量数据库

5. 查询阶段
   ├── 接收查询问题（支持多语言）
   ├── 向量化查询
   ├── 计算相似度（余弦相似度）
   ├── Top-K检索
   └── 返回结果

6. 结果处理阶段
   ├── 格式化结果
   ├── 添加元数据
   └── 返回给调用者
```

## 🎯 性能优化

### 1. 模型管理策略

- **模型懒加载**：首次调用时加载，之后复用（全局单例）
- **模型缓存**：加载后常驻内存，避免重复加载
- ❌ **向量缓存**：不需要（每次HTML都不一样，重新构建）
- ❌ **查询缓存**：不需要

### 2. 批量处理

- 批量向量化chunks（batch_size从config.yaml读取，默认32）
- 使用GPU加速（如果可用）：`device`从config.yaml读取

### 3. 错误处理

- **模型下载失败**：直接终止，返回错误信息
- **HTML解析失败**：部分解析，返回能解析的部分
- **向量化失败**：返回错误，说明具体原因

### 4. 内存管理

- 每次调用结束后释放向量数据（模型常驻内存）
- 不限制HTML大小（去除噪音后文本量不会太大）

## 📊 评估指标

### 检索质量指标

- **准确率（Precision）**：返回的相关chunks / 总返回chunks
- **召回率（Recall）**：返回的相关chunks / 所有相关chunks
- **F1分数**：准确率和召回率的调和平均
- **多语言准确率**：不同语言的检索准确率

### 性能指标

- **向量化时间**：处理HTML并生成向量的时间
- **检索时间**：查询并返回结果的时间
- **内存占用**：向量存储占用的内存（模型约1.2GB + 向量数据）
- **吞吐量**：每秒处理的查询数

## 🚀 实现计划

### ✅ 实现方案确认（已全部确认）

#### 1. 架构设计

**1.1 模型加载策略**
- ✅ **方案：懒加载 + 全局单例**
  - 首次调用时加载模型（约5-10秒）
  - 加载后常驻内存，后续调用复用
  - 使用全局变量或类属性管理模型实例
  - 模型约1.2GB，加载一次后常驻内存

**1.2 向量存储生命周期**
- ✅ **方案：每次调用都重新构建**
  - 不需要缓存机制
  - HTML每次都不一样，重新构建更简单
  - 调用结束后释放向量数据（模型常驻内存）

**1.3 模块组织**
- ✅ **目录结构**：`html_rag/` 目录
- ✅ **集成方式**：作为MCP工具集成到server.py，和其他工具一样使用

**代码结构**：
```
mcp_servers/newsflow_extract/
├── server.py                    # 添加MCP工具定义和调用
├── extractor.py                 # 现有文件
├── html_rag/                    # 新建目录
│   ├── __init__.py
│   ├── html_parser.py          # HTML解析与清理
│   ├── chunker.py              # 文本分块
│   ├── embedder.py             # 向量化（模型管理）
│   ├── vector_store.py         # 内存向量存储
│   └── retriever.py            # 检索逻辑 + 结果合并
└── HTML_RAG_技术方案.md
```

#### 2. 性能与资源

**2.1 HTML大小限制**
- ✅ **不限制大小**
  - 去除噪音后文本量不会太大
  - 不需要设置大小限制

**2.2 并发处理**
- ✅ **一次只处理一个HTML**
  - 不需要并发支持
  - 简化实现，避免竞争条件

**2.3 内存管理**
- ✅ **暂不需要内存监控**
  - 不实现内存监控功能
  - 每次调用结束后释放向量数据（模型常驻内存）

#### 3. 错误处理

**3.1 模型下载失败**
- ✅ **直接终止任务，返回错误**
  - 返回明确的错误信息
  - 不降级，不重试
  - 错误类型：`MODEL_LOAD_FAILED`

**3.2 HTML解析失败**
- ✅ **部分解析**
  - 能解析多少算多少
  - 返回解析成功的部分
  - 错误类型：`HTML_PARSE_FAILED`（部分成功时仍返回结果）

**3.3 向量化失败**
- ✅ **直接返回错误，说明错误原因**
  - 返回详细的错误信息
  - 包含错误类型和原因
  - 错误类型：`EMBEDDING_FAILED`

#### 4. 配置支持

**4.1 模型选择**
- ✅ **支持在config.yaml中配置**
  - `html_rag.embedding.model_name`（默认：`paraphrase-multilingual-mpnet-base-v2`）
  - `html_rag.embedding.device`（默认：`cpu`）
  - `html_rag.embedding.batch_size`（默认：32）
  - `html_rag.embedding.normalize_embeddings`（默认：true）

**4.2 分块参数**
- ✅ **支持在config.yaml中配置**
  - `html_rag.chunking.min_chunk_size`（默认：100）
  - `html_rag.chunking.max_chunk_size`（默认：1000）
  - `html_rag.chunking.chunk_overlap`（默认：50）
  - `html_rag.chunking.prefer_semantic`（默认：true）
  - `html_rag.chunking.fallback_to_paragraph`（默认：true）

**4.3 检索参数**
- ✅ **支持在config.yaml中配置**
  - `html_rag.retrieval.default_top_k`（默认：3）
  - `html_rag.retrieval.default_min_similarity`（默认：0.3）
  - `html_rag.retrieval.merge_results`（默认：true）
  - **参数优先级**：接口参数 > config.yaml配置 > 默认值

#### 5. 功能范围

**5.1 必需功能**
- ✅ HTML解析与清理（支持多语言）
- ✅ 文本分块（语义分块 + 段落分块）
- ✅ 向量化（懒加载模型）
- ✅ 内存向量存储
- ✅ 检索逻辑（余弦相似度）
- ✅ **结果合并**（相邻相关chunks合并）

**5.2 不需要的功能**
- ❌ 语言检测
- ❌ 重排序
- ❌ 持久化
- ❌ 查询缓存

#### 6. 依赖管理

**6.1 依赖更新**
- ✅ **更新requirements.txt**
  - 添加 `sentence-transformers>=2.2.0`
  - 添加 `numpy>=1.24.0`（如果还没有）
  - **不需要**向量数据库（faiss、chromadb）

**6.2 模型下载**
- ✅ **首次下载需要进度提示**
  - 显示下载进度
  - 失败时明确提醒
  - 下载位置：`~/.cache/huggingface/`

#### 7. 集成方式

**7.1 MCP工具集成**
- ✅ **和现有服务保持一致**
  - 使用 `async def call_tool()`
  - 使用 `ThreadPoolExecutor` 处理同步操作
  - 返回 `List[TextContent]`
  - 错误处理格式一致

**7.2 日志**
- ✅ **不需要详细日志**
  - 基本错误日志即可
  - 不需要性能监控日志

### 实现步骤

#### 第一阶段：核心功能实现
1. 创建 `html_rag/` 目录结构
2. 实现HTML解析与清理（`html_parser.py`）
3. 实现文本分块（`chunker.py`）
4. 实现向量化（`embedder.py`）- 懒加载模型
5. 实现内存向量存储（`vector_store.py`）
6. 实现基础检索逻辑（`retriever.py`）

#### 第二阶段：完善功能
1. 实现结果合并功能
2. 实现配置加载逻辑
3. 完善错误处理
4. 添加模型下载进度提示

#### 第三阶段：集成与测试
1. 在server.py中添加MCP工具定义
2. 实现call_tool处理逻辑
3. 更新config.yaml配置示例
4. 更新requirements.txt
5. 基本功能验证

### 配置文件示例

**config.yaml需要添加的配置**：
```yaml
# HTML RAG配置
html_rag:
  # Embedding模型配置
  embedding:
    model_name: "paraphrase-multilingual-mpnet-base-v2"  # 模型名称
    device: "cpu"  # "cpu" 或 "cuda"（如果支持GPU）
    batch_size: 32  # 批量处理大小
    normalize_embeddings: true  # L2归一化
  
  # 分块配置
  chunking:
    min_chunk_size: 100  # 最小chunk字符数
    max_chunk_size: 1000  # 最大chunk字符数
    chunk_overlap: 50  # chunk重叠字符数
    prefer_semantic: true  # 优先使用语义分块
    fallback_to_paragraph: true  # 语义分块失败时使用段落分块
  
  # 检索配置
  retrieval:
    default_top_k: 3  # 默认返回的chunk数量
    default_min_similarity: 0.3  # 默认最小相似度阈值
    merge_results: true  # 是否合并相邻相关chunks
```

### 依赖更新

**requirements.txt需要添加**：
```python
# HTML RAG检索工具依赖
sentence-transformers>=2.2.0
numpy>=1.24.0  # 如果还没有
```

## 🔍 潜在问题与解决方案

### 问题1：HTML结构复杂，分块困难

**解决方案**：
- 使用多种分块策略的组合
- 提供fallback机制
- 允许用户自定义分块规则

### 问题2：向量化速度慢

**解决方案**：
- 使用批量处理（batch_size=32）
- GPU加速（如果可用）
- 缓存已向量化的内容
- 如果速度要求高，可以使用更轻量的 `paraphrase-multilingual-MiniLM-L12-v2` 模型

### 问题3：检索结果不准确

**解决方案**：
- 调整chunk大小
- 使用更好的embedding模型（已使用mpnet-base-v2）
- 实现重排序机制
- 增加相似度阈值
- 针对特定语言优化分块策略

### 问题4：内存占用过大

**解决方案**：
- 模型约1.2GB，需要足够内存
- 使用更轻量的 embedding 模型（如 MiniLM）
- 流式处理大HTML
- 定期清理缓存

### 问题5：多语言支持问题

**解决方案**：
- 使用 `paraphrase-multilingual-mpnet-base-v2` 模型，支持50+语言
- 确保文本编码为UTF-8
- 测试不同语言的检索效果
- 如果某些语言效果不好，考虑使用专门的语言模型

## 📝 接口设计

### MCP工具接口

```python
Tool(
    name="retrieve_relevant_html_chunks",
    description="从HTML文本中检索与查询问题最相关的文本块。使用RAG架构，将HTML分块并向量化，通过相似度检索返回最相关的内容。支持多语言HTML和查询（50+语言）。",
    inputSchema={
        "type": "object",
        "properties": {
            "html_text": {
                "type": "string",
                "description": "HTML结构的文本内容（支持多语言）"
            },
            "query": {
                "type": "string",
                "description": "查询问题，用于检索相关文本块（支持多语言，如中文、英文、日文等）"
            },
            "top_k": {
                "type": "integer",
                "description": "返回最相关的K个文本块（可选，默认从config.yaml读取，最终默认3）"
            },
            "min_similarity": {
                "type": "number",
                "description": "最小相似度阈值（0-1，可选，默认从config.yaml读取，最终默认0.3）"
            }
        },
        "required": ["html_text", "query"]
    }
)
```

**参数优先级**：
1. 接口参数（如果提供）
2. config.yaml配置
3. 默认值

### 返回格式

**成功返回**：
```json
{
    "query": "这个网页的主要内容是什么？",
    "results": [
        {
            "chunk_id": "chunk_001",
            "text": "这是最相关的文本内容...（可能包含合并的相邻chunks）",
            "similarity": 0.85,
            "html_tag": "article",
            "position": 150,
            "parent_context": "主要章节"
        }
    ],
    "total_chunks": 25,
    "retrieval_time": 0.123,
    "success": true
}
```

**错误返回**：
```json
{
    "success": false,
    "error": "错误原因描述",
    "error_type": "MODEL_LOAD_FAILED" | "HTML_PARSE_FAILED" | "EMBEDDING_FAILED" | "RETRIEVAL_FAILED",
    "query": "原始查询问题",
    "results": []
}
```

### 多语言查询示例

```python
# 中文查询
retrieve_relevant_html_chunks(
    html_text=html_content,
    query="这篇文章的主要观点是什么？"
)

# 英文查询
retrieve_relevant_html_chunks(
    html_text=html_content,
    query="What is the main idea of this article?"
)

# 日文查询
retrieve_relevant_html_chunks(
    html_text=html_content,
    query="この記事の主なポイントは何ですか？"
)
```

## 🔗 参考资源

- [sentence-transformers文档](https://www.sbert.net/)
- [paraphrase-multilingual-mpnet-base-v2模型](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2)
- [RAG论文](https://arxiv.org/abs/2005.11401)
- [Chroma文档](https://www.trychroma.com/)

## 📌 注意事项

### 实现注意事项

1. **模型选择**：默认使用 `paraphrase-multilingual-mpnet-base-v2`，支持50+语言，质量高
2. **内存要求**：模型约1.2GB，需要足够内存（模型常驻内存）
3. **模型加载**：首次调用时会加载模型（约5-10秒），之后复用（懒加载 + 全局单例）
4. **模型下载**：首次使用时会自动下载模型（约1.2GB），需要网络连接，有进度提示，失败时返回错误
5. **配置管理**：所有参数支持在config.yaml中配置，接口参数优先于配置文件
6. **错误处理**：
   - 模型下载失败：直接终止，返回错误（`MODEL_LOAD_FAILED`）
   - HTML解析失败：部分解析，返回能解析的部分
   - 向量化失败：返回错误，说明原因（`EMBEDDING_FAILED`）
7. **结果合并**：相邻相关chunks会自动合并返回（必需功能）
8. **向量存储**：每次调用重新构建，不缓存（因为HTML每次都不一样）
9. **并发处理**：一次只处理一个HTML，不需要并发支持
10. **HTML大小**：不限制大小（去除噪音后文本量不会太大）
11. **内存监控**：暂不需要内存监控功能
12. **日志**：不需要详细日志，基本错误日志即可

### 实现清单

**代码结构**：
```
mcp_servers/newsflow_extract/
├── server.py                    # 添加MCP工具定义和调用
├── extractor.py                 # 现有文件
├── html_rag/                    # 新建目录
│   ├── __init__.py
│   ├── html_parser.py          # HTML解析与清理
│   ├── chunker.py              # 文本分块
│   ├── embedder.py             # 向量化（模型管理）
│   ├── vector_store.py         # 内存向量存储
│   └── retriever.py            # 检索逻辑 + 结果合并
└── HTML_RAG_技术方案.md
```

**配置文件更新**：在config.yaml中添加html_rag配置节（见上方配置示例）

**依赖更新**：在requirements.txt中添加sentence-transformers和numpy

**MCP工具集成**：在server.py的list_tools()和call_tool()中添加工具定义和处理逻辑

## 🎯 总结

本方案采用 `paraphrase-multilingual-mpnet-base-v2` 作为默认embedding模型，该模型：
- ✅ 支持50+语言，满足多语言HTML检索需求
- ✅ 质量高，基于mpnet架构
- ✅ 开源免费，无需API key
- ✅ 本地运行，速度快
- ✅ 官方维护，稳定可靠

该方案能够有效处理多语言HTML内容，通过RAG架构实现高质量的文本检索功能。
