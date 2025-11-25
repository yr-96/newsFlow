# NewsFlow 安装说明

## Python版本要求

**重要**：MCP SDK 需要 **Python 3.10+**

当前系统Python版本：Python 3.9.6

### 选项1：升级Python（推荐）

```bash
# macOS (使用Homebrew)
brew install python@3.10
# 或
brew install python@3.11

# 使用pyenv管理多个Python版本（推荐）
brew install pyenv
pyenv install 3.11.0
pyenv local 3.11.0
```

### 选项2：使用Python 3.10+运行（如果已安装）

```bash
# 检查是否有Python 3.10+
python3.10 --version
python3.11 --version

# 如果存在，使用该版本安装依赖
python3.10 -m pip install -r requirements.txt
```

## 已安装的依赖

以下依赖已成功安装（兼容Python 3.9）：

- ✅ selenium >= 4.0.0
- ✅ beautifulsoup4 >= 4.12.0
- ✅ pyyaml >= 6.0
- ✅ webdriver-manager >= 4.0.0

## 待安装的依赖

以下依赖需要Python 3.10+：

- ⚠️ mcp[cli] >= 1.0.0

## 安装步骤

### 1. 升级Python后安装所有依赖

```bash
# 升级到Python 3.10+后
pip install -r requirements.txt
```

### 2. 或者手动安装MCP SDK

```bash
# 如果已升级Python
pip install mcp[cli]

# 或使用官方包名
pip install @modelcontextprotocol/server-python
```

## 验证安装

安装完成后，可以启动MCP服务器验证安装是否成功：

```bash
cd /Users/hunliji/project/newsFlow
python3.11 -m mcp_servers.newsflow_extract.server
```

如果服务器能够正常启动（看到日志输出且没有错误），说明所有依赖已正确安装。

## 故障排除

### 问题：MCP SDK安装失败

**原因**：Python版本过低（需要3.10+）

**解决**：
1. 升级Python到3.10+
2. 或等待MCP SDK发布支持Python 3.9的版本（可能不会）

### 问题：ChromeDriver下载失败

**解决**：
- 检查网络连接
- 使用代理或镜像源
- 手动下载ChromeDriver并放在PATH中

### 问题：Chrome浏览器未安装

**解决**：
```bash
# macOS
brew install --cask google-chrome

# Linux
sudo apt-get install google-chrome-stable
```

