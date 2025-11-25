# Markdown写入服务 (newsflow-writer)

## 服务概述

`newsflow-writer` 是一个MCP服务，用于创建日期文件夹并保存Markdown文件。该服务按照需求文档的格式保存文章内容，包含文章原标题、AI简短摘要、详细概括和原文链接。

## 功能说明

### 核心功能
- 创建以日期命名的文件夹（YYYY-MM-DD格式）
- 保存Markdown文件到对应日期文件夹
- 文件名安全处理（去除特殊字符）
- 按照需求文档的格式组织内容
- **缓存功能**：每天维护一个JSON缓存文件，记录已分析的文章信息

### 技术方案

#### 1. 日期文件夹管理
按照日期（YYYY-MM-DD格式）创建文件夹，如果文件夹不存在则自动创建。

```python
from datetime import datetime
import os

date_str = datetime.now().strftime("%Y-%m-%d")
folder_path = os.path.join(base_dir, date_str)
os.makedirs(folder_path, exist_ok=True)
```

#### 2. 文件名安全处理
去除或替换文件名中的特殊字符，确保文件名符合操作系统要求。

```python
import re

def sanitize_filename(filename):
    # 移除或替换不允许的字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制长度
    if len(filename) > 100:
        filename = filename[:100]
    return filename
```

#### 3. Markdown格式生成
按照需求文档的格式生成Markdown内容：

```markdown
**原名**
文章标题（格式：中文标题（英文原标题））

**ai总结内容**
AI生成的约200字简短摘要，采用轻松、口语化的表达方式，包含文章核心观点、关键信息和主要结论。语气自然放松，像朋友聊天一样娓娓道来，在合适的位置适当添加表情符号，让总结更生动有趣。

**详细概括**
AI生成的500-800字详细文章概括，包含以下结构化的部分：
- **背景信息**：简要介绍文章主题和背景
- **核心要点**：列出2-5个主要观点
- **关键信息**：重要的数据、事实、发现或具体案例
- **影响分析**：这个内容可能带来的影响、意义或启示
- **结论**：文章的核心结论或主要观点总结
保持轻松、口语化的风格，但内容要更加详细和全面，确保是对文章的深入分析。

**原文链接**
[文章原标题](文章原始URL)
```

**注意**：`detailed_summary` 字段是必需的，必须生成，不能为空。

#### 4. 文件写入
将Markdown内容写入文件，如果文件已存在则覆盖。

## MCP工具定义

### save_markdown_file

**描述**：保存Markdown文件到日期文件夹，支持缓存功能，自动检查文章是否已分析过

**输入参数**：
- `title` (string, 必需): 文件名（文章标题，格式：中文标题（英文原标题），会进行安全处理）
- `original_title` (string, 必需): 文章原标题（格式：中文标题（英文原标题），Markdown中的"原名"）
- `summary` (string, 必需): AI生成的约200字简短摘要（Markdown中的"ai总结内容"），采用轻松、口语化的表达方式
- `detailed_summary` (string, 必需): AI生成的500-800字详细概括（**必须生成，不能为空**），包含背景信息、核心要点、关键信息、影响分析和结论
- `url` (string, 必需): 文章原始URL（Markdown中的"原文链接"）
- `date` (string, 可选): 日期（YYYY-MM-DD格式），默认为今天
- `chinese_title` (string, 可选): 中文标题（用于缓存），如果不提供则使用title作为默认值
- `skip_if_exists` (boolean, 可选): 如果文章已分析过是否跳过保存（默认false，会覆盖保存）

**返回结果**：
```json
{
  "path": "保存路径（完整路径）",
  "filename": "文件名.md",
  "date_folder": "日期文件夹路径",
  "success": true,
  "cached": false
}
```

**实现要点**：
1. 如果`date`为None，使用今天的日期（YYYY-MM-DD）
2. 创建日期文件夹（如果不存在）：`output/YYYY-MM-DD/`
3. 文件名安全处理（去除特殊字符、限制长度）
4. **缓存检查**：保存前检查文章是否已分析过（通过URL判断）
5. 如果文件已存在且`skip_if_exists=true`，跳过保存；否则覆盖保存
6. 保存成功后，自动更新缓存文件（`articles_cache.json`）
7. 按照需求文档的格式写入Markdown内容

**Markdown格式**：
- 第一行：`**原名**`
- 第二行：文章标题（格式：中文标题（英文原标题））
- 空行
- 第四行：`**ai总结内容**`
- 第五行：AI生成的约200字简短摘要，轻松、口语化的表达方式
- 空行
- 第七行：`**详细概括**`
- 第八行：AI生成的500-800字详细概括，包含背景信息、核心要点、关键信息、影响分析和结论
- 空行
- 第十行：`**原文链接**`
- 第十一行：`[文章原标题](文章原始URL)` （Markdown链接格式）

### create_date_folder

**描述**：创建日期文件夹

**输入参数**：
- `date` (string, 可选): 日期（YYYY-MM-DD格式），默认为今天

**返回结果**：
```json
{
  "path": "文件夹完整路径",
  "success": true
}
```

## MCP资源定义

### config

**描述**：读取配置文件

**URI**：`config://config.yaml`

**返回**：YAML配置文件的完整内容

**用途**：供Cursor读取网站列表等配置信息

## 依赖要求

- Python 3.8+
- pyyaml >= 6.0

## 配置说明

服务使用配置文件 `config.yaml`：

```yaml
websites:
  - name: "示例新闻网站1"
    url: "https://news.example1.com"
    enabled: true

output:
  base_dir: "./output"  # 输出基础目录
  date_format: "%Y-%m-%d"  # 日期格式
```

## 缓存功能

### 缓存文件格式

每天会在日期文件夹下自动创建和维护一个 `articles_cache.json` 文件，记录已分析的文章信息：

```json
{
  "articles": [
    {
      "original_title": "文章原标题",
      "chinese_title": "中文标题",
      "url": "文章链接"
    }
  ]
}
```

### 缓存功能特点

1. **自动创建**：每次保存文章时自动创建或更新缓存文件
2. **去重判断**：通过URL判断文章是否已分析过，避免重复处理
3. **自动更新**：如果文章已存在但信息有更新，会自动更新缓存
4. **容错处理**：缓存文件读写失败不会影响主功能，只记录警告日志

### 使用场景

- 批量处理新闻时，可以快速检查哪些文章已经分析过
- 支持`skip_if_exists`参数，已分析的文章可以选择跳过保存
- 可以通过读取缓存文件获取当天所有已分析文章的列表

## 注意事项

1. **文件覆盖**：如果同名文件已存在且`skip_if_exists=false`，会覆盖保存（获取最新内容）
2. **文件名长度**：文件名限制在100字符以内，超长会被截断
3. **特殊字符**：Windows系统不允许的字符（`< > : " / \ | ? *`）会被替换为下划线
4. **路径安全**：确保输出路径在指定目录内，避免路径遍历攻击
5. **日期格式**：统一使用YYYY-MM-DD格式
6. **缓存文件**：缓存文件为JSON格式，手动编辑时需注意格式正确性

## 文件结构

```
newsflow_writer/
├── server.py      # MCP服务器入口
├── __init__.py
├── writer.py      # 文件写入逻辑
└── README.md      # 本说明文档
```

## 开发状态

- [x] 技术方案设计
- [ ] MCP服务器框架搭建
- [ ] 日期文件夹创建逻辑
- [ ] 文件名安全处理
- [ ] Markdown格式生成
- [ ] 文件写入逻辑
- [ ] 配置资源实现
- [ ] 错误处理
- [ ] 单元测试
- [ ] Cursor集成测试

