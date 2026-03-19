# NewsFlow - 新闻聚合和智能摘要系统

## 📖 项目简介

NewsFlow 是一个基于 MCP (Model Context Protocol) 架构的新闻聚合和智能摘要系统。系统通过 Cursor AI 助手调用 MCP 服务，自动从多个新闻网站提取文章，生成结构化的 Markdown 摘要文档，并可自动发送邮件摘要。

## ✨ 核心特性

- 🤖 **AI驱动的链接识别**：通过 Cursor AI 智能识别新闻链接，自动过滤非新闻内容
- 📝 **智能摘要生成**：自动生成一两百字的文章摘要和500-800字的详细概括
- 📁 **按日期归档**：自动按日期组织文档，便于管理和查找
- 🔗 **支持CSR网站**：使用 Selenium 无头模式支持客户端渲染网站
- 📧 **邮件摘要发送**：支持将当日新闻摘要以HTML格式发送到多个邮箱
- 💾 **智能缓存**：自动缓存已分析文章，避免重复处理
- 🎯 **无需外部AI API**：所有AI功能由 Cursor 提供
- ☁️ **OSS上传支持**：支持上传文件到阿里云OSS、腾讯云COS、AWS S3、MinIO等

## 🏗️ 系统架构

```
Cursor AI助手
    ↓ MCP Protocol
MCP服务: newsflow-extract (URL提取 + Markdown写入 + 邮件发送)
    ↓ 返回链接列表
Cursor AI (判断文章链接，生成总结)
    ↓ MCP Protocol
MCP服务工具调用 (保存Markdown、发送邮件)
    ↓
输出文件 (output/YYYY-MM-DD/*.md)
```

## 📁 项目结构

```
newsFlow/
├── mcp_servers/              # MCP服务目录
│   ├── newsflow_extract/     # URL提取服务（集成所有功能）
│   │   ├── server.py         # MCP服务器入口（提供所有工具）
│   │   ├── extractor.py      # 链接提取逻辑（Selenium）
│   │   └── README.md         # 服务说明文档
│   └── newsflow_writer/      # Markdown写入服务模块
│       ├── writer.py         # 文件写入、缓存、邮件功能
│       ├── markdown.py       # Markdown生成和解析
│       ├── html_generator.py # HTML邮件生成
│       ├── email_sender.py   # 邮件发送
│       ├── cache.py          # 文章缓存管理
│       ├── file_utils.py     # 文件工具函数
│       ├── oss_uploader.py  # OSS上传功能
│       └── README.md         # 服务说明文档
├── shared/                   # 共享模块
│   ├── config.py            # 配置加载
│   └── logger.py            # 日志工具
├── .cursor/                  # Cursor配置
│   ├── commands/            # Cursor命令定义
│   │   └── newflow.md       # NewsFlow执行指令
│   └── mcp.json             # MCP项目配置（可选）
├── config.yaml               # 配置文件（网站列表、邮件配置等）
├── requirements.txt          # Python依赖
├── output/                   # 输出目录
│   └── YYYY-MM-DD/          # 按日期组织的Markdown文件
└── README.md                 # 本文件
```

## 🚀 快速开始

### 1. 环境要求

- **Python 3.10+**（MCP SDK要求）
- **Google Chrome浏览器**（用于Selenium）
- **Cursor IDE**（用于AI功能）

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd newsFlow

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

### 4. 配置项目

编辑 `config.yaml` 文件：

```yaml
# 网站列表
websites:
  - name: "Hacker News"
    url: "https://news.ycombinator.com/newest"
    enabled: true
  - name: "TLDR"
    url: "https://tldr.tech"
    enabled: true

# 输出配置
output:
  base_dir: "./output"
  date_format: "%Y-%m-%d"

# 邮件配置（可选，用于发送摘要）
email:
  smtp_server: "smtp.qq.com"
  smtp_port: 587
  sender_email: "your-email@example.com"
  sender_password: "your-password"
  sender_name: "NewsFlow"
  use_tls: true
  recipient_emails:
    - "recipient@example.com"

# OSS配置（可选）
oss:
  provider: "aliyun"  # aliyun, tencent, aws, minio
  # ... 其他OSS配置
```

### 5. 配置Cursor MCP服务

#### 方法1：使用项目配置（推荐）

项目已包含 `.cursor/mcp.json` 配置文件，Cursor会自动读取。

#### 方法2：全局配置

在Cursor中配置MCP服务器，配置文件位置：
- **macOS/Linux**: `~/.cursor/mcp.json`
- **Windows**: `%USERPROFILE%\.cursor\mcp.json`

```json
{
  "mcpServers": {
    "newsflow-extract": {
      "command": "/path/to/newsFlow/venv/bin/python",
      "args": ["-m", "mcp_servers.newsflow_extract.server"],
      "cwd": "/path/to/newsFlow"
    }
  }
}
```

**注意**：将 `/path/to/newsFlow` 替换为你的实际项目路径。

#### 方法3：通过Cursor设置界面

1. 打开Cursor设置（`Cmd+,` 或 `Ctrl+,`）
2. 搜索 "MCP" 或 "Model Context Protocol"
3. 添加MCP服务器：
   - **名称**: `newsflow-extract`
   - **类型**: `stdio`
   - **命令**: `/path/to/newsFlow/venv/bin/python`
   - **参数**: `["-m", "mcp_servers.newsflow_extract.server"]`
   - **工作目录**: `/path/to/newsFlow`

### 6. 重启Cursor

配置完成后：
1. **完全退出Cursor**（`Cmd+Q` 或 `Alt+F4`，不要只是关闭窗口）
2. **重新启动Cursor**
3. **验证MCP服务连接**：在设置中查看MCP服务器状态

### 7. 使用

在Cursor中发送指令，例如：

```
执行newflow
```

或更具体的指令：

```
帮我运行NewsFlow，从配置的网站提取新闻并生成Markdown摘要
```

## 📚 使用示例

### 示例1：提取并保存单篇文章

1. Cursor调用 `extract_links_from_url` 提取网站链接
2. AI识别文章链接
3. AI生成文章摘要（简短摘要 + 详细概括）
4. Cursor调用 `save_markdown_file` 保存Markdown文件

### 示例2：批量处理多篇文章

1. 遍历配置的网站列表
2. 对每个网站提取链接
3. AI过滤并识别文章链接（每个网站至少5篇）
4. 批量生成摘要并保存（自动使用缓存去重）

### 示例3：发送邮件摘要

处理完当日新闻后，可以发送邮件摘要：

```
发送今天（2025-12-12）的新闻摘要到配置的邮箱
```

或在Cursor中使用MCP工具：
- `send_email_from_date_folder` - 发送指定日期的新闻摘要邮件

## 🛠️ MCP工具列表

NewsFlow提供了以下MCP工具：

### URL提取工具
- **`extract_links_from_url`**：从指定URL提取所有链接（支持CSR网站）

### Markdown写入工具
- **`save_markdown_file`**：保存Markdown文件到日期文件夹（支持缓存）
- **`create_date_folder`**：创建日期文件夹（YYYY-MM-DD格式）

### 邮件工具
- **`send_email_from_date_folder`**：读取日期文件夹中的所有Markdown文件，生成HTML邮件并发送到多个收件人

### OSS上传工具（可选）
- **`upload_file_to_oss`**：上传文件到OSS（支持阿里云OSS、腾讯云COS、AWS S3、MinIO）

## 📄 输出文件格式

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

## 🔧 功能特性详解

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
- 自动解析文章信息（原名、AI总结、详细概括、原文链接）
- 生成格式化的HTML邮件
- 详细概括以折叠形式展示，点击可展开
- 支持多个收件人（可单独配置或使用配置文件默认值）
- 支持SMTP/SSL/TLS多种邮件协议

### 4. 文件名安全处理
- 自动去除特殊字符（Windows系统限制字符）
- 限制文件名长度（最大100字符）
- 支持中英文标题

### 5. OSS上传功能（可选）
- 支持多种OSS提供商：阿里云OSS、腾讯云COS、AWS S3、MinIO
- 自动配置管理
- 支持自定义OSS键（路径）

## 🔍 故障排除

### 问题1：MCP SDK安装失败

**错误信息**：`Requires-Python >=3.10`

**解决**：确保使用Python 3.10+安装

```bash
# 检查Python版本
python3 --version

# 使用正确版本安装
python3.10 -m pip install mcp[cli]
# 或
python3.11 -m pip install mcp[cli]
```

### 问题2：Cursor找不到MCP服务器

**可能原因**：
- 配置文件路径错误
- Python路径错误
- 工作目录不存在

**解决方法**：

1. **确认配置文件位置**：
   ```bash
   # 全局配置
   ~/.cursor/mcp.json
   
   # 项目配置（推荐）
   /path/to/newsFlow/.cursor/mcp.json
   ```

2. **验证Python路径**：
   ```bash
   # 验证虚拟环境Python存在
   test -f /path/to/newsFlow/venv/bin/python && echo "✅ Python路径正确"
   
   # 验证MCP SDK已安装
   /path/to/newsFlow/venv/bin/python -c "import mcp; print('✅ MCP SDK已安装')"
   ```

3. **检查配置文件格式**：
   ```bash
   python3 -m json.tool ~/.cursor/mcp.json
   ```

4. **完全重启Cursor**：
   - 按 `Cmd+Q` 完全退出Cursor（不要只是关闭窗口）
   - 等待几秒钟
   - 重新启动Cursor

### 问题3：MCP服务器启动失败

**可能原因**：
- MCP SDK未安装
- 依赖缺失
- Python版本不兼容

**解决方法**：

```bash
cd /path/to/newsFlow
source venv/bin/activate

# 检查MCP SDK
python -c "import mcp; print('MCP SDK OK')"

# 重新安装依赖
pip install -r requirements.txt

# 验证所有依赖
python -c "import mcp, selenium, bs4, yaml, webdriver_manager; print('所有依赖OK')"
```

### 问题4：ChromeDriver问题

**解决**：
- webdriver-manager会自动下载，确保网络连接正常
- 首次运行可能需要一些时间
- 如果下载失败，检查网络连接或使用代理

### 问题5：邮件发送失败

**可能原因**：
- SMTP配置错误
- 邮箱授权码未设置
- 网络连接问题

**解决方法**：
1. 检查 `config.yaml` 中的邮件配置
2. 确保使用正确的SMTP服务器和端口
3. 对于Gmail，需要使用应用专用密码（App Password）
4. 检查防火墙设置

## 📖 详细文档

- **[MCP服务文档](mcp_servers/newsflow_extract/README.md)**：URL提取服务详细说明
- **[Writer服务文档](mcp_servers/newsflow_writer/README.md)**：Markdown写入服务详细说明
- **[OSS上传文档](mcp_servers/newsflow_writer/OSS_README.md)**：OSS上传功能说明

## 🛠️ 技术栈

- **Python 3.10+**：运行环境（MCP SDK要求）
- **MCP (Model Context Protocol)**：Cursor与服务间的通信协议
- **Selenium 4.0+**：浏览器自动化（无头模式，支持CSR网站）
- **BeautifulSoup4**：HTML解析和链接提取
- **PyYAML**：配置文件解析
- **webdriver-manager**：ChromeDriver自动管理
- **Cursor AI**：AI能力提供者（链接识别、摘要生成）

## 📝 许可证

本项目为个人项目，仅供学习和研究使用。

## 🤝 贡献

欢迎提出问题和建议！

## 📞 获取帮助

如果遇到问题：
1. 查看本文档的故障排除部分
2. 查看MCP服务详细文档
3. 检查Cursor的错误日志（`Help` → `Toggle Developer Tools`）
