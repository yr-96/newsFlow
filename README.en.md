# NewsFlow - News Aggregation and Intelligent Summary System

## 📖 Project Overview

NewsFlow is a news aggregation and intelligent summary system based on the MCP (Model Context Protocol) architecture. It uses Cursor AI to invoke MCP services, automatically extracts articles from multiple news websites, generates structured Markdown summaries, and can send email digests.

## ✨ Key Features

- 🤖 **AI-Powered Link Recognition**: Cursor AI intelligently identifies news links and filters out non-news content
- 📝 **Smart Summary Generation**: Automatically generates ~200-word article summaries and 500-800 word detailed summaries
- 📁 **Date-Based Archiving**: Organizes documents by date for easy management and retrieval
- 🔗 **CSR Website Support**: Uses Selenium headless mode to support client-side rendered websites
- 📧 **Email Digest**: Sends daily news summaries in HTML format to multiple recipients
- 💾 **Smart Caching**: Caches analyzed articles to avoid duplicate processing
- 🎯 **No External AI API**: All AI capabilities are provided by Cursor
- ☁️ **OSS Upload Support**: Supports Aliyun OSS, Tencent COS, AWS S3, MinIO, and more

## 🏗️ System Architecture

```
Cursor AI Assistant
    ↓ MCP Protocol
MCP Service: newsflow-extract (URL extraction + Markdown writing + Email sending)
    ↓ Returns link list
Cursor AI (identifies article links, generates summaries)
    ↓ MCP Protocol
MCP tool calls (save Markdown, send email)
    ↓
Output files (output/YYYY-MM-DD/*.md)
```

## 📁 Project Structure

```
newsFlow/
├── mcp_servers/              # MCP services directory
│   ├── newsflow_extract/     # URL extraction service (integrated features)
│   │   ├── server.py         # MCP server entry (provides all tools)
│   │   ├── extractor.py      # Link extraction logic (Selenium)
│   │   └── README.md         # Service documentation
│   └── newsflow_writer/      # Markdown writing service module
│       ├── writer.py         # File writing, caching, email functions
│       ├── markdown.py       # Markdown generation and parsing
│       ├── html_generator.py # HTML email generation
│       ├── email_sender.py   # Email sending
│       ├── cache.py          # Article cache management
│       ├── file_utils.py     # File utility functions
│       ├── oss_uploader.py  # OSS upload functionality
│       └── README.md         # Service documentation
├── shared/                   # Shared modules
│   ├── config.py            # Configuration loading
│   └── logger.py            # Logging utilities
├── .cursor/                  # Cursor configuration
│   ├── commands/            # Cursor command definitions
│   │   └── newflow.md       # NewsFlow execution instructions
│   └── mcp.json             # MCP project config (optional)
├── config.yaml               # Configuration (websites, email, etc.)
├── requirements.txt         # Python dependencies
├── output/                   # Output directory
│   └── YYYY-MM-DD/          # Markdown files organized by date
└── README.md                 # This file
```

## 🚀 Quick Start

### 1. Requirements

- **Python 3.10+** (MCP SDK requirement)
- **Google Chrome** (for Selenium)
- **Cursor IDE** (for AI features)

### 2. Install Dependencies

```bash
# Clone the project
git clone <repository-url>
cd newsFlow

# Create virtual environment (recommended)
python3.10 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Chrome Browser

The URL extraction service uses **Selenium** in headless mode to access websites, supporting client-side rendered (CSR) sites.

**Note**:
- **Chrome Browser**: Google Chrome must be installed
- **ChromeDriver**: No manual installation needed; `webdriver-manager` auto-downloads on first run
- **Headless Mode**: Runs without opening a browser window

```bash
# macOS
brew install --cask google-chrome

# Linux (Ubuntu/Debian)
sudo apt-get install google-chrome-stable

# Windows
# Download from https://www.google.com/chrome/
```

### 4. Configure the Project

Edit `config.yaml`:

```yaml
# Website list
websites:
  - name: "Hacker News"
    url: "https://news.ycombinator.com/newest"
    enabled: true
  - name: "TLDR"
    url: "https://tldr.tech"
    enabled: true

# Output config
output:
  base_dir: "./output"
  date_format: "%Y-%m-%d"

# Email config (optional, for sending digests)
email:
  smtp_server: "smtp.qq.com"
  smtp_port: 587
  sender_email: "your-email@example.com"
  sender_password: "your-password"
  sender_name: "NewsFlow"
  use_tls: true
  recipient_emails:
    - "recipient@example.com"

# OSS config (optional)
oss:
  provider: "aliyun"  # aliyun, tencent, aws, minio
  # ... other OSS config
```

### 5. Configure Cursor MCP Service

#### Method 1: Project Config (Recommended)

The project includes `.cursor/mcp.json`; Cursor will read it automatically.

#### Method 2: Global Config

Configure MCP server in Cursor:
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

**Note**: Replace `/path/to/newsFlow` with your actual project path.

#### Method 3: Via Cursor Settings UI

1. Open Cursor Settings (`Cmd+,` or `Ctrl+,`)
2. Search for "MCP" or "Model Context Protocol"
3. Add MCP server:
   - **Name**: `newsflow-extract`
   - **Type**: `stdio`
   - **Command**: `/path/to/newsFlow/venv/bin/python`
   - **Args**: `["-m", "mcp_servers.newsflow_extract.server"]`
   - **CWD**: `/path/to/newsFlow`

### 6. Restart Cursor

After configuration:
1. **Fully quit Cursor** (`Cmd+Q` or `Alt+F4`, not just close the window)
2. **Restart Cursor**
3. **Verify MCP connection**: Check MCP server status in settings

### 7. Usage

Send a command in Cursor, for example:

```
执行newflow
```

Or more specific:

```
Run NewsFlow: extract news from configured websites and generate Markdown summaries
```

## 📚 Usage Examples

### Example 1: Extract and Save a Single Article

1. Cursor calls `extract_links_from_url` to extract links
2. AI identifies article links
3. AI generates summary (short + detailed)
4. Cursor calls `save_markdown_file` to save the Markdown file

### Example 2: Batch Process Multiple Articles

1. Iterate over configured website list
2. Extract links from each site
3. AI filters and identifies article links (at least 5 per site)
4. Batch generate summaries and save (auto cache deduplication)

### Example 3: Send Email Digest

After processing daily news:

```
Send today's (2025-12-12) news digest to configured email
```

Or use MCP tool in Cursor:
- `send_email_from_date_folder` - Send news digest email for a given date

## 🛠️ MCP Tools

### URL Extraction
- **`extract_links_from_url`**: Extract all links from a URL (supports CSR sites)

### Markdown Writing
- **`save_markdown_file`**: Save Markdown to date folder (with caching)
- **`create_date_folder`**: Create date folder (YYYY-MM-DD format)

### Email
- **`send_email_from_date_folder`**: Read all Markdown files in a date folder, generate HTML email, and send to multiple recipients

### OSS Upload (Optional)
- **`upload_file_to_oss`**: Upload file to OSS (Aliyun OSS, Tencent COS, AWS S3, MinIO)

## 📄 Output Format

Generated Markdown format:

```markdown
**原名**
Article title (format: Chinese title (English original title))

**ai总结内容**
~200-word AI summary, casual and conversational, with core points, key info, and main conclusions. Natural tone with emojis where appropriate.

**详细概括**
500-800 word detailed summary with:
- **Background**: Brief intro to topic
- **Key Points**: 2-5 main points
- **Key Information**: Important data, facts, findings
- **Impact**: Implications and significance
- **Conclusion**: Core conclusion

**原文链接**
[Original title](Original URL)
```

**Note**: The detailed summary field is required and cannot be empty.

## 🔧 Feature Details

### 1. Smart Link Extraction
- Selenium headless browser, waits for JavaScript rendering
- Extracts all `<a>` tag links
- Converts relative paths to absolute
- Filters invalid links (javascript:, mailto:, etc.)

### 2. Article Caching
- Daily JSON cache file (`articles_cache.json`)
- URL-based deduplication
- `skip_if_exists` parameter support

### 3. Email Digest
- Reads all Markdown files in date folder
- Parses article info (title, AI summary, detailed summary, link)
- Generates formatted HTML email
- Collapsible detailed summaries
- Multiple recipients, SMTP/SSL/TLS support

### 4. Safe Filenames
- Removes special characters (Windows restrictions)
- Max 100 character filename length
- Supports Chinese and English titles

### 5. OSS Upload (Optional)
- Supports Aliyun OSS, Tencent COS, AWS S3, MinIO
- Configurable
- Custom OSS key (path) support

## 🔍 Troubleshooting

### Issue 1: MCP SDK Install Fails

**Error**: `Requires-Python >=3.10`

**Fix**: Use Python 3.10+

```bash
python3 --version
python3.10 -m pip install mcp[cli]
```

### Issue 2: Cursor Can't Find MCP Server

**Causes**: Wrong config path, wrong Python path, missing cwd

**Fix**:
1. Check config location: `~/.cursor/mcp.json` or `./.cursor/mcp.json`
2. Verify Python path and MCP SDK
3. Validate JSON: `python3 -m json.tool ~/.cursor/mcp.json`
4. Fully restart Cursor (`Cmd+Q`)

### Issue 3: MCP Server Won't Start

**Fix**:
```bash
cd /path/to/newsFlow
source venv/bin/activate
pip install -r requirements.txt
python -c "import mcp, selenium, bs4, yaml, webdriver_manager; print('OK')"
```

### Issue 4: ChromeDriver

- webdriver-manager auto-downloads; ensure network access
- First run may take time

### Issue 5: Email Send Fails

- Check `config.yaml` email settings
- Use correct SMTP server and port
- For Gmail, use App Password
- Check firewall

## 📖 Documentation

- **[MCP Service](mcp_servers/newsflow_extract/README.md)**: URL extraction service
- **[Writer Service](mcp_servers/newsflow_writer/README.md)**: Markdown writing service
- **[OSS Upload](mcp_servers/newsflow_writer/OSS_README.md)**: OSS upload guide

## 🛠️ Tech Stack

- **Python 3.10+**: Runtime (MCP SDK requirement)
- **MCP**: Cursor-service communication protocol
- **Selenium 4.0+**: Browser automation (headless, CSR support)
- **BeautifulSoup4**: HTML parsing
- **PyYAML**: Config parsing
- **webdriver-manager**: ChromeDriver management
- **Cursor AI**: AI for link recognition and summary generation

## 📝 License

Personal project for learning and research.

## 🤝 Contributing

Issues and suggestions welcome!

## 📞 Help

1. Check the troubleshooting section above
2. Read MCP service docs
3. Check Cursor logs: `Help` → `Toggle Developer Tools`
