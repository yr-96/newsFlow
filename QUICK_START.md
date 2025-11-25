# 快速启动指南

## ⚠️ 重要提示

MCP SDK需要 **Python 3.10+**，但当前系统是 **Python 3.9.6**

在启动MCP服务之前，需要先升级Python。

## 已完成的工作

✅ **基础依赖已安装**：
- selenium (4.36.0)
- beautifulsoup4 (4.14.2)
- PyYAML (6.0.3)
- webdriver-manager (4.0.2)

✅ **代码已修复**：
- 修复了Selenium WebDriver API调用
- extractor模块可以独立测试运行

✅ **Cursor配置文件已创建**：
- 位置：`~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
- 已包含newsflow-extract服务配置

## 下一步操作

### 1. 升级Python（必需）

MCP SDK需要Python 3.10+。请选择以下方式之一：

**选项A：安装Homebrew后安装Python 3.11**
```bash
# 安装Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Python 3.11
brew install python@3.11
```

**选项B：从Python官网下载安装**
访问：https://www.python.org/downloads/

### 2. 安装MCP SDK

升级Python后：
```bash
# 使用Python 3.11安装
python3.11 -m pip install mcp[cli]

# 验证安装
python3.11 -c "import mcp; print('MCP SDK安装成功')"
```

### 3. 更新Cursor配置文件

编辑 `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`：

```json
{
  "mcpServers": {
    "newsflow-extract": {
      "command": "python3.11",
      "args": ["-m", "mcp_servers.newsflow_extract.server"],
      "cwd": "/Users/hunliji/project/newsFlow"
    }
  }
}
```

**注意**：将 `python3.11` 替换为你安装的Python 3.10+版本路径。

### 4. 测试MCP服务器

```bash
cd /Users/hunliji/project/newsFlow
python3.11 -m mcp_servers.newsflow_extract.server
```

如果看到日志输出且没有错误，说明服务器可以启动。

### 5. 重启Cursor

1. 完全退出Cursor（Cmd+Q）
2. 重新启动Cursor
3. MCP服务应该会自动连接


## 详细文档

- **完整安装指南**：查看 `SETUP_MCP.md`
- **使用说明**：查看 `CURSOR_USAGE.md`
- **MCP服务文档**：查看 `mcp_servers/newsflow_extract/README.md`

