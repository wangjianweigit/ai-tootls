#!/bin/bash
# 海心AI工具集 - 自动化打包脚本
# 基于 tools.json 自动发现并打包所有工具

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_NAME="haixin-tools-$(date +%Y%m%d-%H%M%S).tar.gz"
TEMP_DIR="/tmp/haixin-tools-package"

echo "╔════════════════════════════════════════════════╗"
echo "║        海心AI工具集 - 自动化打包                 ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 检查 tools.json
if [ ! -f "$SCRIPT_DIR/tools.json" ]; then
    echo "❌ 错误：未找到 tools.json"
    exit 1
fi

# 检查 jq 是否安装（用于解析 JSON）
if ! command -v jq &> /dev/null; then
    echo "⚠️  未安装 jq，使用 Python 解析 JSON"
    USE_PYTHON=true
else
    USE_PYTHON=false
fi

# 清理临时目录
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR/haixin-tools"

echo "📦 开始打包..."
echo ""

# 函数：使用 Python 解析 tools.json
parse_tools_python() {
    python3 << 'PYTHON_SCRIPT'
import json
import sys

with open('tools.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

for tool in config.get('tools', []):
    if not tool.get('enabled', True):
        continue
    
    # 工具目录
    directory = tool.get('directory')
    if not directory:
        # 尝试从 id 推断（处理常见命名）
        tool_id = tool.get('id', '')
        # ai-model-compare → ai-model-compare
        # excel-parse-tools → excelParseTools
        if 'excel' in tool_id:
            directory = 'excelParseTools'
        else:
            directory = tool_id
    
    # 排除规则
    excludes = tool.get('packaging', {}).get('exclude', [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.venv',
        'venv/',
        '*.log',
        '*.pid',
        'logs/',
        'data/*.sqlite3',
        'data/*.db'
    ])
    
    # 输出格式：directory|exclude1,exclude2,exclude3
    print(f"{directory}|{','.join(excludes)}")
PYTHON_SCRIPT
}

# 函数：使用 jq 解析 tools.json
parse_tools_jq() {
    jq -r '.tools[] | select(.enabled != false) | 
        (.directory // .id) + "|" + 
        ((.packaging.exclude // [
            "__pycache__",
            "*.pyc",
            ".venv",
            "*.log",
            "*.pid"
        ]) | join(","))' "$SCRIPT_DIR/tools.json"
}

# 解析工具配置
cd "$SCRIPT_DIR"
if [ "$USE_PYTHON" = true ]; then
    TOOLS=$(parse_tools_python)
else
    TOOLS=$(parse_tools_jq)
fi

# 打包每个工具
echo "🔍 发现以下工具："
echo "$TOOLS" | while IFS='|' read -r directory excludes; do
    echo "  📁 $directory"
done
echo ""

# 执行打包
echo "$TOOLS" | while IFS='|' read -r directory excludes; do
    if [ -z "$directory" ]; then
        continue
    fi
    
    echo "✓ 打包: $directory"
    
    if [ -d "$SCRIPT_DIR/$directory" ]; then
        # 构建 rsync 排除参数
        exclude_args=""
        IFS=',' read -ra EXCLUDE_LIST <<< "$excludes"
        for exclude in "${EXCLUDE_LIST[@]}"; do
            exclude_args="$exclude_args --exclude='$exclude'"
        done
        
        # 执行 rsync
        eval rsync -av $exclude_args \
            "$SCRIPT_DIR/$directory/" \
            "$TEMP_DIR/haixin-tools/$directory/" > /dev/null
        
        echo "  ✅ 已打包: $directory"
    else
        echo "  ⚠️  目录不存在，跳过: $directory"
        mkdir -p "$TEMP_DIR/haixin-tools/$directory"
    fi
done

echo ""
echo "✓ 复制配置文件..."
cp "$SCRIPT_DIR/tools.json" "$TEMP_DIR/haixin-tools/"
[ -f "$SCRIPT_DIR/start-all.sh" ] && cp "$SCRIPT_DIR/start-all.sh" "$TEMP_DIR/haixin-tools/"
[ -f "$SCRIPT_DIR/stop-all.sh" ] && cp "$SCRIPT_DIR/stop-all.sh" "$TEMP_DIR/haixin-tools/"
[ -f "$SCRIPT_DIR/aistarfish-tools.nginx.conf" ] && cp "$SCRIPT_DIR/aistarfish-tools.nginx.conf" "$TEMP_DIR/haixin-tools/"
[ -f "$SCRIPT_DIR/README.md" ] && cp "$SCRIPT_DIR/README.md" "$TEMP_DIR/haixin-tools/"

echo "✓ 创建必要目录..."
# 从 tools.json 读取工具并创建数据目录
echo "$TOOLS" | while IFS='|' read -r directory _; do
    if [ -n "$directory" ] && [ -d "$TEMP_DIR/haixin-tools/$directory" ]; then
        mkdir -p "$TEMP_DIR/haixin-tools/$directory/data" 2>/dev/null || true
        mkdir -p "$TEMP_DIR/haixin-tools/$directory/logs" 2>/dev/null || true
    fi
done

echo "✓ 打包中..."
cd "$TEMP_DIR"
tar -czf "$SCRIPT_DIR/$PACKAGE_NAME" haixin-tools/

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║              打包完成！                        ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "📦 打包文件: $PACKAGE_NAME"
echo "📊 文件大小: $(du -h "$SCRIPT_DIR/$PACKAGE_NAME" | cut -f1)"
echo ""
echo "📋 包含的工具："
echo "$TOOLS" | while IFS='|' read -r directory _; do
    echo "  ✅ $directory"
done
echo ""

# 远程服务器配置
REMOTE_HOST="192.168.51.67"
REMOTE_USER="admin"
REMOTE_DIR="/home/admin"

# 询问是否上传
echo "═══════════════════════════════════════════════════"
read -p "是否上传到远程服务器 ${REMOTE_USER}@${REMOTE_HOST}? (y/n): " -n 1 -r
echo ""
echo "═══════════════════════════════════════════════════"

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    read -sp "请输入远程服务器密码: " REMOTE_PASS
    echo ""
    echo ""
    
    echo "【上传到远程服务器】"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if command -v sshpass &> /dev/null; then
        echo "✓ 使用 sshpass 自动上传..."
        sshpass -p "$REMOTE_PASS" scp "$SCRIPT_DIR/$PACKAGE_NAME" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ 上传成功！"
            echo ""
            echo "建议接下来运行："
            echo "  ./remote-docker-deploy.sh  # 自动部署 Docker 容器"
            echo ""
        else
            echo "❌ 上传失败"
        fi
    else
        echo "⚠️  未安装 sshpass，使用交互式上传"
        scp "$SCRIPT_DIR/$PACKAGE_NAME" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
    fi
else
    echo ""
    echo "手动部署步骤："
    echo "  1. 上传: scp $PACKAGE_NAME ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
    echo "  2. 部署: ./remote-docker-deploy.sh"
    echo ""
fi

# 清理
rm -rf "$TEMP_DIR"

echo ""
echo "提示："
echo "  • 手动打包: ./package.sh"
echo "  • 自动打包: ./package-auto.sh (本脚本)"
echo "  • 查看打包指南: cat PACKAGING_GUIDE.md"
echo ""

