#!/bin/bash
# 一键安装Python 3.11、MCP SDK并启动服务

set -e

PROJECT_DIR="/Users/hunliji/project/newsFlow"
cd "$PROJECT_DIR"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║      NewsFlow MCP服务 - 一键安装和启动脚本                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查是否已有Python 3.10+
PYTHON_CMD=""
for py in python3.11 python3.10 python3.12; do
    if command -v $py &> /dev/null; then
        if $py -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            if $py -c "import mcp" 2>/dev/null; then
                PYTHON_CMD=$py
                echo "✅ 发现已安装的Python和MCP SDK: $PYTHON_CMD"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "📦 需要安装Python 3.11和MCP SDK..."
    echo ""
    
    # 检查Homebrew
    if ! command -v brew &> /dev/null; then
        echo "1️⃣  安装Homebrew（需要输入密码）..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加Homebrew到PATH
        if [ -f "/opt/homebrew/bin/brew" ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -f "/usr/local/bin/brew" ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
    
    echo ""
    echo "2️⃣  安装Python 3.11..."
    brew install python@3.11
    
    PYTHON_CMD="python3.11"
    
    echo ""
    echo "3️⃣  安装MCP SDK..."
    $PYTHON_CMD -m pip install --user mcp[cli]
    
    echo ""
    echo "✅ 安装完成！"
fi

echo ""
echo "🚀 启动MCP服务..."
echo "   按 Ctrl+C 停止服务"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# 启动服务
$PYTHON_CMD -m mcp_servers.newsflow_extract.server

