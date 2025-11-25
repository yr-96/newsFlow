# newsflow-extract 使用说明

## 运行MCP服务器

### 方式1：使用启动脚本（推荐）

```bash
# 在项目根目录运行
./start_newsflow_extract.sh
```

### 方式2：作为模块运行（需要激活虚拟环境）

```bash
# 先激活虚拟环境
source venv/bin/activate

# 然后运行
python -m mcp_servers.newsflow_extract.server
```

### 方式3：直接使用虚拟环境的 Python

```bash
# 在项目根目录
venv/bin/python -m mcp_servers.newsflow_extract.server
```

**重要提示**：
- ❌ **不要**直接运行 `python mcp_servers/newsflow_extract/server.py`（会因相对导入失败）
- ✅ **必须**使用 `python -m` 方式作为模块运行
- ✅ **必须**使用虚拟环境中的 Python（已安装所有依赖）

## 注意事项

1. **MCP SDK版本**：如果遇到导入错误，可能需要根据实际的MCP Python SDK调整导入语句
2. **ChromeDriver**：首次运行时会自动下载，需要网络连接
3. **日志输出**：日志输出到stderr，不会干扰MCP协议的stdio通信

## 调试

如果MCP服务器无法正常启动，可以：

1. 检查依赖是否安装：
   ```bash
   pip install -r requirements.txt
   ```

2. 检查Chrome是否安装：
   ```bash
   # macOS
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
   ```

