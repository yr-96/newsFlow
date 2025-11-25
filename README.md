# NewsFlow - 新闻聚合和智能摘要系统

## 项目简介

NewsFlow 是一个基于 MCP (Model Context Protocol) 架构的新闻聚合和智能摘要系统。系统通过 Cursor AI 助手调用 MCP 服务，自动从多个新闻网站提取文章，生成结构化的 Markdown 摘要文档，并可自动发送邮件摘要。

## 核心特性

- 🤖 **AI驱动的链接识别**：通过 Cursor AI 智能识别新闻链接，自动过滤非新闻内容
- 📝 **智能摘要生成**：自动生成一两百字的文章摘要
- 📁 **按日期归档**：自动按日期组织文档，便于管理和查找
- 🔗 **支持CSR网站**：使用 Selenium 无头模式支持客户端渲染网站
- 📧 **邮件摘要发送**：支持将当日新闻摘要以HTML格式发送到多个邮箱
- 💾 **智能缓存**：自动缓存已分析文章，避免重复处理
- 🎯 **无需外部AI API**：所有AI功能由 Cursor 提供

## 系统架构

```
Cursor AI助手
    ↓ MCP Protocol
MCP服务1: newsflow-extract (URL提取)
    ↓ 返回链接列表
Cursor AI (判断文章链接，生成总结)
    ↓ MCP Protocol
MCP服务2: newsflow-writer (保存Markdown)
    ↓
输出文件 (output/YYYY-MM-DD/*.md)
```

## 项目结构

```
newsflow/
├── mcp_servers/              # MCP服务目录
│   ├── newsflow_extract/     # URL提取服务（集成writer功能）
│   │   ├── server.py         # MCP服务器入口（提供所有工具）
│   │   ├── __init__.py
│   │   ├── extractor.py      # 链接提取逻辑（Selenium）
│   │   ├── README.md         # 服务说明文档
│   │   └── USAGE.md          # 使用说明
│   └── newsflow_writer/      # Markdown写入服务模块
│       ├── __init__.py
│       ├── writer.py         # 文件写入、缓存、邮件功能
│       └── README.md         # 服务说明文档
├── shared/                   # 共享模块
│   └── logger.py             # 日志工具
├── config.yaml               # 配置文件（网站列表、邮件配置等）
├── requirements.txt          # Python依赖
├── output/                   # 输出目录
│   └── YYYY-MM-DD/          # 按日期组织的Markdown文件
├── README.md                 # 本文件
├── CURSOR_USAGE.md          # Cursor使用说明
├── SETUP_MCP.md             # MCP服务安装配置指南
├── QUICK_START.md           # 快速启动指南
└── start_newsflow_extract.sh # 启动脚本
```

## 快速开始

### 1. 环境要求

- **Python 3.10+**（MCP SDK要求）
- **Google Chrome浏览器**（用于Selenium）

### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3.10 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 安装Chrome浏览器

URL提取服务使用 **Selenium** 无头模式访问网站，支持客户端渲染（CSR）网站。

**注意**：
- **Chrome浏览器**：系统需要安装Google Chrome
- **ChromeDriver**：无需手动安装，`webdriver-manager`会在首次运行时自动下载对应版本
- **无头模式**：使用headless模式，不会打开浏览器窗口

```bash
# macOS
brew install --cask google-chrome

# Linux (Ubuntu/Debian)
sudo apt-get install google-chrome-stable

# Windows
# 从 https://www.google.com/chrome/ 下载安装
```

### 4. 配置

编辑 `config.yaml` 文件：

```yaml
websites:
  - name: "Hacker News"
    url: "https://news.ycombinator.com/newest"
    enabled: true

output:
  base_dir: "./output"
  date_format: "%Y-%m-%d"

# 邮件配置（可选，用于发送摘要）
email:
  smtp_server: "smtp.qq.com"
  smtp_port: 465
  sender_email: "your-email@example.com"
  sender_password: "your-password"
  recipient_emails:
    - "recipient@example.com"
```

### 5. 配置Cursor MCP服务

在Cursor中配置MCP服务器（详见 [CURSOR_USAGE.md](CURSOR_USAGE.md) 或 [SETUP_MCP.md](SETUP_MCP.md)）

配置文件位置：`~/Library/Application Support/Cursor/User/globalStorage/mcp.json`

```json
{
  "mcpServers": {
    "newsflow-extract": {
      "command": "python3",
      "args": ["-m", "mcp_servers.newsflow_extract.server"],
      "cwd": "/path/to/newsFlow"
    }
  }
}
```

### 6. 使用

在Cursor中发送指令，例如：
```
帮我运行NewsFlow，从配置的网站提取新闻并生成Markdown摘要
```

或更具体的指令：
```
从Hacker News提取最新的技术新闻，识别文章链接，生成摘要并保存到今天的日期文件夹
```

### 7. 发送邮件摘要（可选）

处理完新闻后，可以发送邮件摘要：

```
发送今天（2025-11-02）的新闻摘要到配置的邮箱
```

或在Cursor中使用MCP工具：
- `send_email_from_date_folder` - 发送指定日期的新闻摘要邮件

## 使用示例

### 示例1：提取并保存单篇文章

1. Cursor调用 `extract_links_from_url` 提取网站链接
2. AI识别文章链接
3. AI生成文章摘要
4. Cursor调用 `save_markdown_file` 保存Markdown文件

### 示例2：批量处理多篇文章

1. 遍历配置的网站列表
2. 对每个网站提取链接
3. AI过滤并识别文章链接
4. 批量生成摘要并保存（自动使用缓存去重）

### 示例3：发送邮件摘要

1. 处理完当日新闻后
2. 调用 `send_email_from_date_folder` 工具
3. 系统自动读取当日文件夹中的所有Markdown文件
4. 生成HTML格式邮件并发送到配置的邮箱

## 文档说明

- **[需求文档.md](需求文档.md)**：项目功能需求和验收标准
- **[技术文档.md](技术文档.md)**：详细的技术实现方案
- **[CURSOR_USAGE.md](CURSOR_USAGE.md)**：Cursor使用说明和最佳实践
- **[技术方案对比.md](技术方案对比.md)**：技术方案选择分析

## MCP服务文档

- **[URL提取服务](mcp_servers/newsflow_extract/README.md)**：链接提取功能说明
- **[Markdown写入服务](mcp_servers/newsflow_writer/README.md)**：文件保存功能说明

## MCP工具列表

NewsFlow提供了以下MCP工具：

### URL提取工具
- **`extract_links_from_url`**：从指定URL提取所有链接（支持CSR网站）

### Markdown写入工具
- **`save_markdown_file`**：保存Markdown文件到日期文件夹（支持缓存）
- **`create_date_folder`**：创建日期文件夹（YYYY-MM-DD格式）

### 邮件工具
- **`send_email_from_date_folder`**：读取日期文件夹中的所有Markdown文件，生成HTML邮件并发送到多个收件人

## 技术栈

- **Python 3.10+**：运行环境（MCP SDK要求）
- **MCP (Model Context Protocol)**：Cursor与服务间的通信协议
- **Selenium 4.0+**：浏览器自动化（无头模式，支持CSR网站）
- **BeautifulSoup4**：HTML解析和链接提取
- **PyYAML**：配置文件解析
- **webdriver-manager**：ChromeDriver自动管理
- **Cursor AI**：AI能力提供者（链接识别、摘要生成）

## 功能特性详解

### 1. 智能链接提取
- 使用Selenium无头浏览器访问网站，等待JavaScript渲染完成
- 自动提取所有`<a>`标签链接
- 自动将相对路径转换为绝对路径
- 过滤无效链接（javascript:、mailto:等）

### 2. 文章缓存机制
- 每天维护一个JSON缓存文件（`articles_cache.json`）
- 通过URL判断文章是否已分析，避免重复处理
- 支持`skip_if_exists`参数控制是否跳过已分析文章

### 3. 邮件摘要功能
- 读取指定日期文件夹中的所有Markdown文件
- 自动解析文章信息（原名、AI总结、原文链接）
- 生成格式化的HTML邮件
- 支持多个收件人（可单独配置或使用配置文件默认值）
- 支持SMTP/SSL/TLS多种邮件协议

### 4. 文件名安全处理
- 自动去除特殊字符（Windows系统限制字符）
- 限制文件名长度（最大100字符）
- 支持中英文标题

## 输出文件格式

生成的Markdown文件格式：

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

## 开发状态

- [x] 项目规划和技术方案设计
- [x] 项目结构搭建
- [x] MCP服务实现
  - [x] URL提取服务（Selenium + BeautifulSoup）
  - [x] Markdown写入服务（文件管理 + 缓存）
  - [x] 邮件发送服务
- [x] MCP服务文档编写
- [x] Cursor集成测试
- [x] 使用文档完善
- [ ] 单元测试（计划中）

## 许可证

本项目为个人项目，仅供学习和研究使用。

## 贡献

欢迎提出问题和建议！

