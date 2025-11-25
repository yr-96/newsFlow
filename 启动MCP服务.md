# 启动MCP服务 - 快速指南

## 🎯 目标

启动 `newsflow-extract` MCP服务并在Cursor中注册。

## ⚠️ 当前状态

- ✅ 基础依赖已安装（selenium, beautifulsoup4等）
- ✅ MCP服务器代码已实现
- ✅ Cursor配置文件已创建
- ❌ **缺少：Python 3.10+ 和 MCP SDK**

## 📋 安装步骤

### 方法1：使用Homebrew安装（推荐，最快）

**步骤1：安装Homebrew**

打开终端，运行：
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安装过程中会提示输入密码。

**步骤2：安装Python 3.11**
```bash
brew install python@3.11
```

**步骤3：安装MCP SDK**
```bash
python3.11 -m pip install --user mcp[cli]
```

**步骤4：验证安装**
```bash
python3.11 -c "import mcp; print('MCP SDK安装成功')"
```

### 方法2：从Python官网安装

**步骤1：下载Python 3.11**

访问：https://www.python.org/downloads/release/python-3110/

下载 macOS 安装包（.pkg文件）

**步骤2：安装Python**

双击下载的.pkg文件，按照提示安装。

**步骤3：安装MCP SDK**

打开终端，运行：
```bash
# 查找Python 3.11的路径（通常在 /usr/local/bin/ 或 /Library/Frameworks/Python.framework/）
python3.11 -m pip install --user mcp[cli]
```

如果没有 `python3.11` 命令，尝试：
```bash
# 找到Python 3.11的完整路径
/usr/local/bin/python3.11 -m pip install --user mcp[cli]
# 或
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pip install --user mcp[cli]
```

## 🚀 启动MCP服务

安装完成后，有两种方式启动：

### 方式1：使用启动脚本

```bash
cd /Users/hunliji/project/newsFlow
./start_mcp.sh
```

### 方式2：直接运行

```bash
cd /Users/hunliji/project/newsFlow
python3.11 -m mcp_servers.newsflow_extract.server
```

如果看到日志输出且没有错误，说明服务器已启动！

## ⚙️ 更新Cursor配置

安装Python 3.11后，需要更新Cursor配置文件：

**编辑文件**：`~/Library/Application Support/Cursor/User/globalStorage/mcp.json`

**更新内容**：
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

**注意**：如果Python 3.11不在PATH中，需要使用完整路径：
```json
{
  "mcpServers": {
    "newsflow-extract": {
      "command": "/usr/local/bin/python3.11",
      "args": ["-m", "mcp_servers.newsflow_extract.server"],
      "cwd": "/Users/hunliji/project/newsFlow"
    }
  }
}
```

## ✅ 验证

### 1. 验证Python版本
```bash
python3.11 --version
# 应该显示：Python 3.11.x
```

### 2. 验证MCP SDK
```bash
python3.11 -c "import mcp; print('✅ MCP SDK已安装')"
```

### 3. 启动MCP服务器
```bash
cd /Users/hunliji/project/newsFlow
python3.11 -m mcp_servers.newsflow_extract.server
```

如果看到类似这样的输出（没有错误），说明成功：
```
2025-11-01 17:30:41,352 - __main__ - INFO - 启动 NewsFlow Extract MCP Server...
```

## 🔄 重启Cursor

配置完成后：
1. 完全退出Cursor（Cmd+Q）
2. 重新启动Cursor
3. MCP服务应该自动连接

## 🆘 故障排除

### 问题：找不到python3.11命令

**解决**：
1. 查找Python 3.11的安装路径：
   ```bash
   ls -la /usr/local/bin/python* /opt/homebrew/bin/python* 2>/dev/null
   ```
2. 在Cursor配置中使用完整路径

### 问题：MCP SDK安装失败

**解决**：
```bash
# 使用完整路径安装
python3.11 -m pip install --upgrade pip
python3.11 -m pip install mcp[cli]
```

### 问题：Cursor无法连接MCP服务器

**检查**：
1. 配置文件路径是否正确
2. Python路径是否正确
3. 查看Cursor的错误日志

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看详细文档：`SETUP_MCP.md`
2. 查看使用说明：`CURSOR_USAGE.md`
3. 查看快速启动：`QUICK_START.md`

