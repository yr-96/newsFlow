#!/bin/bash
# 启动 newsflow-extract MCP 服务器的便捷脚本

cd "$(dirname "$0")"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ 已激活虚拟环境"
else
    echo "❌ 虚拟环境不存在，请先创建: python3 -m venv venv"
    exit 1
fi

# 检查 MCP SDK
if ! python -c "import mcp" 2>/dev/null; then
    echo "❌ MCP SDK 未安装"
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

echo ""
echo "🚀 启动 NewsFlow Extract MCP 服务器..."
echo "   按 Ctrl+C 停止服务器"
echo "   注意：MCP 服务器通过 stdio 通信，看起来像'卡住'是正常的"
echo ""

# 使用模块方式运行（必须，否则相对导入会失败）
python -m mcp_servers.newsflow_extract.server

