#!/bin/bash
# 启动MCP服务的脚本

cd "$(dirname "$0")"

echo "=== 启动NewsFlow Extract MCP服务 ==="
echo ""

# 查找Python 3.10+
PYTHON_CMD=""
for py in python3.12 python3.11 python3.10 python3; do
    if command -v $py &> /dev/null; then
        VERSION=$($py --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            # 检查MCP SDK
            if $py -c "import mcp" 2>/dev/null; then
                PYTHON_CMD=$py
                echo "✅ 使用 $PYTHON_CMD ($($py --version))"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ 未找到Python 3.10+或MCP SDK未安装"
    echo ""
    echo "请先运行安装脚本："
    echo "  ./install_python.sh"
    echo ""
    echo "或手动安装："
    echo "  1. 安装Python 3.10+（推荐3.11）"
    echo "  2. 运行: python3.11 -m pip install mcp[cli]"
    exit 1
fi

echo ""
echo "🚀 启动MCP服务器..."
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动服务器
$PYTHON_CMD -m mcp_servers.newsflow_extract.server

