# NewsFlow - Cursor使用说明

## 简介

NewsFlow是一个新闻聚合和智能摘要系统，通过MCP服务架构实现。系统由两个MCP服务和Cursor AI助手协同工作，自动从多个新闻网站提取文章并生成Markdown格式的摘要文档。

## 系统架构

```
Cursor AI助手
    ↓ (调用MCP服务)
MCP服务1: newsflow-extract (URL提取)
    ↓ (返回链接列表)
Cursor AI (判断文章链接，生成总结)
    ↓ (调用MCP服务)
MCP服务2: newsflow-writer (保存Markdown)
    ↓
输出文件 (output/YYYY-MM-DD/*.md)
```

## 前置准备

### 1. 安装依赖

```bash
cd /Users/hunliji/project/newsFlow
pip install -r requirements.txt
```

### 2. 安装Chrome浏览器

**说明**：
- URL提取服务使用Selenium无头模式（headless）运行，不会打开浏览器窗口
- ChromeDriver由`webdriver-manager`自动管理，无需手动安装

**macOS**:
```bash
brew install --cask google-chrome
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install google-chrome-stable
```

**Windows**:
从 [Google Chrome官网](https://www.google.com/chrome/) 下载安装

**注意**：ChromeDriver会在首次运行时自动下载，无需手动安装。

### 3. 创建配置文件

```bash
cp config.yaml.example config.yaml
# 编辑config.yaml，添加要监控的新闻网站
```

**config.yaml示例**:
```yaml
websites:
  - name: "示例新闻网站1"
    url: "https://news.example1.com"
    enabled: true
  - name: "示例新闻网站2"
    url: "https://news.example2.com"
    enabled: true

output:
  base_dir: "./output"
  date_format: "%Y-%m-%d"
```

## Cursor配置

### 配置MCP服务器

在Cursor中配置MCP服务器连接。配置文件位置：
- macOS: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
- 或通过Cursor设置界面配置

**配置内容**：
```json
{
  "mcpServers": {
    "newsflow-extract": {
      "command": "python",
      "args": ["-m", "mcp_servers.newsflow_extract.server"],
      "cwd": "/Users/hunliji/project/newsFlow"
    },
    "newsflow-writer": {
      "command": "python",
      "args": ["-m", "mcp_servers.newsflow_writer.server"],
      "cwd": "/Users/hunliji/project/newsFlow"
    }
  }
}
```

**注意**：将`/Users/hunliji/project/newsFlow`替换为你的实际项目路径。

### 重启Cursor

配置完成后，重启Cursor以使MCP服务生效。

## 使用方法

### 基础使用流程

通过Cursor对话方式执行任务：

#### 1. 启动任务

在Cursor中发送指令：

```
帮我运行NewsFlow，从配置的网站提取新闻并生成Markdown
```

#### 2. Cursor执行流程

Cursor会自动执行以下步骤：

1. **读取配置**
   - 通过MCP资源读取`config.yaml`
   - 获取网站列表

2. **提取链接**
   - 对每个启用的网站：
     - 调用 `newsflow-extract::extract_links_from_url(url)`
     - 获取所有链接列表

3. **处理链接**
   - 对每个链接：
     - Cursor直接访问链接URL读取内容
     - Cursor使用AI判断：是否为文章链接？
     - **如果是文章链接**：
       - Cursor读取文章完整内容
       - Cursor生成一两百字总结
       - 调用 `newsflow-writer::save_markdown_file` 保存文件
     - **如果不是文章链接**：跳过

4. **完成**
   - 输出统计信息（处理的网站数、提取的文章数等）

### 高级用法

#### 自定义日期文件夹

```
帮我提取新闻并保存到2024-01-15这个日期文件夹
```

#### 处理特定网站

```
只从配置中的第一个网站提取新闻
```

#### 查看已处理的文章

```
读取output/2024-01-15文件夹下的所有文章
```

## MCP服务说明

### newsflow-extract (URL提取服务)

**功能**：从网站提取所有链接

**工具**：
- `extract_links_from_url(url: str)`：提取指定URL的所有链接

**返回**：
```json
{
  "links": ["url1", "url2", ...],
  "count": 链接数量
}
```

详细说明请参考：[mcp_servers/newsflow_extract/README.md](mcp_servers/newsflow_extract/README.md)

### newsflow-writer (Markdown写入服务)

**功能**：保存Markdown文件

**工具**：
- `save_markdown_file(title, original_title, summary, detailed_summary, url, date=None)`：保存Markdown文件（包含详细概括）
- `create_date_folder(date=None)`：创建日期文件夹

**资源**：
- `config://config.yaml`：读取配置文件

详细说明请参考：[mcp_servers/newsflow_writer/README.md](mcp_servers/newsflow_writer/README.md)

## 输出格式

### 文件结构

```
output/
├── 2024-01-15/
│   ├── 文章标题1.md
│   ├── 文章标题2.md
│   └── ...
└── 2024-01-16/
    └── ...
```

### Markdown格式

每个Markdown文件格式如下：

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

**注意**：`详细概括` 字段是必需的，必须生成，不能为空。

## 常见问题

### 1. MCP服务连接失败

**问题**：Cursor提示无法连接MCP服务

**解决**：
- 检查Python环境是否正确
- 检查依赖是否安装完整（`pip install -r requirements.txt`）
- 检查Cursor配置中的路径是否正确
- 查看Cursor的日志输出获取详细错误信息

### 2. ChromeDriver问题

**问题**：Selenium报错ChromeDriver相关错误

**解决**：
- 使用`webdriver-manager`会自动管理ChromeDriver，首次运行时会自动下载对应版本
- 如果仍有问题，检查Chrome浏览器是否已正确安装
- 确保网络连接正常（首次运行需要下载ChromeDriver）

### 3. 网站访问失败

**问题**：某些网站无法访问或超时

**解决**：
- 检查网络连接
- 某些网站可能有反爬虫机制，需要调整User-Agent
- 可以调整等待时间（在extractor.py中修改`implicitly_wait`参数）

### 4. 链接提取不完整

**问题**：CSR网站的链接没有完全提取

**解决**：
- 当前使用5秒隐式等待，对于加载较慢的网站可能需要增加等待时间
- 部分需要用户交互才能加载的内容无法获取（这是正常限制）

### 5. 文件保存失败

**问题**：Markdown文件保存失败

**解决**：
- 检查output目录权限
- 检查磁盘空间
- 检查文件名是否包含特殊字符（应该会自动处理）

## 最佳实践

1. **定期运行**：建议每天运行一次，获取最新新闻
2. **监控输出**：检查生成的Markdown文件是否符合预期
3. **调整配置**：根据实际需求调整`config.yaml`中的网站列表
4. **日志查看**：关注Cursor输出的日志信息，了解执行过程
5. **性能优化**：处理大量网站时，注意单个网站的链接数量，避免处理时间过长

## 技术支持

- 查看技术文档：[技术文档.md](技术文档.md)
- 查看需求文档：[需求文档.md](需求文档.md)
- MCP服务详细说明：
  - [URL提取服务](mcp_servers/newsflow_extract/README.md)
  - [Markdown写入服务](mcp_servers/newsflow_writer/README.md)

## 开发计划

当前状态：项目结构搭建完成，准备开始编码实现。

下一步：
1. 实现MCP服务框架
2. 实现URL提取功能
3. 实现Markdown写入功能
4. Cursor集成测试

