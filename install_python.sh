#!/bin/bash
# 安装Python 3.11和MCP SDK的脚本

set -e

echo "=== NewsFlow MCP服务 - Python安装脚本 ==="
echo ""

# 检查是否已有Python 3.10+
if command -v python3.11 &> /dev/null; then
    PYTHON_VER="python3.11"
    echo "✅ 发现Python 3.11: $(which $PYTHON_VER)"
elif command -v python3.10 &> /dev/null; then
    PYTHON_VER="python3.10"
    echo "✅ 发现Python 3.10: $(which $PYTHON_VER)"
else
    echo "❌ 未找到Python 3.10+"
    echo ""
    echo "正在尝试安装Homebrew和Python 3.11..."
    echo ""
    
    # 检查Homebrew
    if ! command -v brew &> /dev/null; then
        echo "📦 安装Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加Homebrew到PATH（根据架构）
        if [ -f "/opt/homebrew/bin/brew" ]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -f "/usr/local/bin/brew" ]; then
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
    
    echo "📦 安装Python 3.11..."
    brew install python@3.11
    
    PYTHON_VER="python3.11"
fi

echo ""
echo "=== 安装MCP SDK ==="
echo ""

# 安装MCP SDK
echo "使用 $PYTHON_VER 安装MCP SDK..."
$PYTHON_VER -m pip install --user mcp[cli]

echo ""
echo "=== 验证安装 ==="
echo ""

# 验证
if $PYTHON_VER -c "import mcp; print('✅ MCP SDK安装成功')" 2>/dev/null; then
    echo ""
    echo "🎉 安装完成！"
    echo ""
    echo "Python版本: $($PYTHON_VER --version)"
    echo "Python路径: $(which $PYTHON_VER)"
    echo ""
    echo "现在可以启动MCP服务了："
    echo "  $PYTHON_VER -m mcp_servers.newsflow_extract.server"
    echo ""
    echo "或在Cursor配置中使用: $PYTHON_VER"
else
    echo "❌ MCP SDK安装失败"
    exit 1
fi

