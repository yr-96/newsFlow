# Cursor MCP 服务注册指南

## 📋 当前状态

✅ 配置文件已存在：`~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
✅ 虚拟环境已创建并安装依赖
✅ 配置已更新为使用虚拟环境中的 Python

## 🚀 注册步骤

### 方法 1：配置文件已就绪（当前状态）

配置文件已经复制到正确位置，只需要：

1. **完全退出 Cursor**
   ```bash
   # 按 Cmd+Q 完全退出，不要只是关闭窗口
   ```

2. **重新启动 Cursor**

3. **验证 MCP 服务是否连接**
   - 打开 Cursor 设置（`Cmd+,`）
   - 搜索 "MCP" 或查看状态栏
   - 应该能看到 `newsflow-extract` 服务已连接

### 方法 2：通过 Cursor 设置界面手动配置

如果配置文件方式不工作，可以通过界面配置：

1. **打开 Cursor 设置**
   - 按 `Cmd+,` 打开设置
   - 或者点击左下角齿轮图标

2. **导航到 MCP 配置**
   - 在设置中搜索 "MCP" 或 "Model Context Protocol"
   - 或者找到 "Features" → "Model Context Protocol"

3. **添加 MCP 服务器**
   - 点击 "添加新 MCP 服务器" 或 "+" 按钮
   - 填写以下信息：
     - **名称（Name）**: `newsflow-extract`
     - **类型（Type）**: `stdio`
     - **命令（Command）**: `/Users/hunliji/project/newsFlow/venv/bin/python`
     - **参数（Args）**: `["-m", "mcp_servers.newsflow_extract.server"]`
     - **工作目录（CWD）**: `/Users/hunliji/project/newsFlow`

4. **保存配置**
   - 点击保存
   - Cursor 会自动尝试连接

## 📝 当前配置文件内容

配置文件位置：`~/Library/Application Support/Cursor/User/globalStorage/mcp.json`

```json
{
  "mcpServers": {
    "newsflow-extract": {
      "command": "/Users/hunliji/project/newsFlow/venv/bin/python",
      "args": ["-m", "mcp_servers.newsflow_extract.server"],
      "cwd": "/Users/hunliji/project/newsFlow"
    },
    "newsflow-writer": {
      "command": "/Users/hunliji/project/newsFlow/venv/bin/python",
      "args": ["-m", "mcp_servers.newsflow_writer.server"],
      "cwd": "/Users/hunliji/project/newsFlow"
    }
  }
}
```

## ✅ 验证配置是否正确

### 1. 检查 Python 路径

```bash
# 验证虚拟环境 Python 存在且可执行
test -f /Users/hunliji/project/newsFlow/venv/bin/python && echo "✅ Python 路径正确" || echo "❌ Python 路径错误"

# 验证 MCP SDK 已安装
/Users/hunliji/project/newsFlow/venv/bin/python -c "import mcp; print('✅ MCP SDK 已安装')"
```

### 2. 测试服务器是否可以启动

```bash
cd /Users/hunliji/project/newsFlow
source venv/bin/activate
python -m mcp_servers.newsflow_extract.server
```

如果看到日志输出（没有错误），说明服务器可以正常启动。按 `Ctrl+C` 停止。

### 3. 查看 Cursor 日志

如果服务没有连接，可以查看 Cursor 的错误日志：
- macOS: `~/Library/Logs/Cursor/`
- 或者在 Cursor 中查看开发者工具：`Help` → `Toggle Developer Tools`

## 🔧 故障排除

### 问题 1：Cursor 找不到 MCP 服务器

**可能原因**：
- 配置文件路径错误
- Python 路径错误
- 工作目录不存在

**解决方法**：
```bash
# 1. 验证配置文件存在
ls -la ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json

# 2. 验证 Python 路径
ls -la /Users/hunliji/project/newsFlow/venv/bin/python

# 3. 验证工作目录
ls -la /Users/hunliji/project/newsFlow
```

### 问题 2：MCP 服务器启动失败

**可能原因**：
- MCP SDK 未安装
- 依赖缺失
- Python 版本不兼容

**解决方法**：
```bash
cd /Users/hunliji/project/newsFlow
source venv/bin/activate

# 检查 MCP SDK
python -c "import mcp; print('MCP SDK OK')"

# 重新安装依赖
pip install -r requirements.txt

# 验证所有依赖
python -c "import mcp, selenium, bs4, yaml, webdriver_manager; print('所有依赖 OK')"
```

### 问题 3：配置文件格式错误

**检查 JSON 格式**：
```bash
python3 -m json.tool ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json
```

如果报错，说明 JSON 格式有问题，需要修复。

### 问题 4：权限问题

确保 Python 文件有执行权限：
```bash
chmod +x /Users/hunliji/project/newsFlow/venv/bin/python
```

## 🎯 快速检查清单

完成注册前，确认以下项目：

- [ ] 虚拟环境已创建：`ls venv/bin/python`
- [ ] 依赖已安装：`venv/bin/python -c "import mcp"`
- [ ] 配置文件已复制到正确位置
- [ ] 配置文件中的路径正确（绝对路径）
- [ ] Cursor 已完全重启（Cmd+Q 退出）

## 📞 下一步

配置完成后：

1. **重启 Cursor**（完全退出后重新打开）

2. **验证连接**
   - 在 Cursor 中查看 MCP 服务器状态
   - 或者尝试使用工具：询问 Cursor "帮我从某个网站提取链接"

3. **使用服务**
   ```
   帮我从 https://example.com 提取所有链接
   ```

## 🔄 更新配置

如果需要更新配置，直接编辑配置文件后重启 Cursor：

```bash
# 编辑配置文件
nano ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json

# 或者使用项目中的配置文件
cp /Users/hunliji/project/newsFlow/cursor-mcp-config.json \
   ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json
```

然后重启 Cursor。


