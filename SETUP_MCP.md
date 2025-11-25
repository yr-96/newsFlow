# MCP服务启动和Cursor配置指南

## 前置要求

⚠️ **重要**：MCP SDK需要 **Python 3.10+**

当前系统Python版本：Python 3.9.6

## 步骤1：升级Python到3.10+

### 选项A：使用Homebrew（推荐）

```bash
# 安装Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Python 3.11
brew install python@3.11

# 创建符号链接（如果需要）
brew link python@3.11
```

### 选项B：从Python官网安装

访问 https://www.python.org/downloads/ 下载并安装Python 3.10+

### 选项C：使用pyenv管理多个Python版本

```bash
# 安装pyenv
brew install pyenv

# 安装Python 3.11
pyenv install 3.11.0

# 在项目目录设置本地版本
cd /Users/hunliji/project/newsFlow
pyenv local 3.11.0
```

## 步骤2：安装MCP SDK

升级Python后，使用新版本安装MCP SDK：

```bash
# 如果使用brew安装的Python 3.11
python3.11 -m pip install mcp[cli]

# 或者全局安装
pip3 install mcp[cli]
```

验证安装：

```bash
python3.11 -c "import mcp; print('MCP SDK安装成功')"
```

## 步骤3：测试MCP服务器

```bash
cd /Users/hunliji/project/newsFlow

# 使用Python 3.11运行服务器（如果已安装）
python3.11 -m mcp_servers.newsflow_extract.server

# 或者如果已设置pyenv
python3 -m mcp_servers.newsflow_extract.server
```

如果看到日志输出但没有错误，说明服务器可以启动。

## 步骤4：配置Cursor

### 方法1：通过Cursor设置界面

1. 打开Cursor
2. 按 `Cmd+,` 打开设置
3. 搜索 "MCP" 或 "Model Context Protocol"
4. 添加MCP服务器配置

### 方法2：直接编辑配置文件

配置文件位置：`~/Library/Application Support/Cursor/User/globalStorage/mcp.json`

**注意**：如果文件不存在，需要先创建。

复制项目根目录的 `cursor-mcp-config.json` 到Cursor配置目录：

```bash
# 创建配置目录（如果不存在）
mkdir -p ~/Library/Application\ Support/Cursor/User/globalStorage

# 复制配置文件
cp /Users/hunliji/project/newsFlow/cursor-mcp-config.json \
   ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json
```

**重要**：确保配置文件中的路径正确：
- `command`: 使用正确的Python版本（如 `python3.11` 如果使用brew安装）
- `cwd`: 确保是项目根目录的绝对路径

### 配置文件内容

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

**注意**：
- 如果使用 `pyenv local` 设置了项目Python版本，可以使用 `python3`
- 否则需要使用完整路径或 `python3.11`

## 步骤5：重启Cursor

配置完成后：
1. 完全退出Cursor（Cmd+Q）
2. 重新启动Cursor
3. 检查MCP服务器连接状态

## 验证MCP服务是否运行

在Cursor中，你可以：
1. 查看Cursor的MCP服务器状态（通常在设置或状态栏）
2. 尝试调用MCP工具


## 故障排除

### 问题1：MCP SDK安装失败

**错误信息**：`Requires-Python >=3.10`

**解决**：确保使用Python 3.10+安装

```bash
# 检查Python版本
python3.11 --version

# 使用正确版本安装
python3.11 -m pip install mcp[cli]
```

### 问题2：Cursor找不到MCP服务器

**解决**：
1. 检查配置文件路径是否正确
2. 检查`command`字段是否指向正确的Python可执行文件
3. 检查`cwd`是否是项目根目录的绝对路径
4. 查看Cursor的错误日志

### 问题3：MCP服务器启动失败

**解决**：
1. 检查所有依赖是否安装：
   ```bash
   python3.11 -c "import selenium, bs4, yaml, webdriver_manager, mcp; print('所有依赖OK')"
   ```
3. 查看服务器日志（输出到stderr）

### 问题4：ChromeDriver问题

**解决**：
- webdriver-manager会自动下载，确保网络连接正常
- 首次运行可能需要一些时间

## 快速检查清单

- [ ] Python 3.10+已安装
- [ ] MCP SDK已安装：`python3.11 -c "import mcp"`
- [ ] 所有依赖已安装：`pip3 list | grep -E "selenium|beautifulsoup4|pyyaml|webdriver-manager|mcp"`
- [ ] extractor模块可以测试运行
- [ ] Cursor MCP配置文件已创建
- [ ] 配置文件中的路径正确
- [ ] Cursor已重启

完成以上步骤后，MCP服务应该可以在Cursor中使用了！

