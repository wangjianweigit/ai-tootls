#!/bin/bash
set -e

echo "=========================================="
echo "      海心AI工具集 - 统一启动脚本"
echo "=========================================="

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 读取工具配置
TOOLS_CONFIG="tools.json"

if [ ! -f "$TOOLS_CONFIG" ]; then
    echo -e "${RED}错误: 找不到 tools.json 配置文件${NC}"
    exit 1
fi

# 启动工具函数
start_tool() {
    local tool_name=$1
    local tool_dir=$2
    local start_script=$3
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}启动工具: $tool_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ -d "$tool_dir" ] && [ -f "$tool_dir/$start_script" ]; then
        cd "$tool_dir"
        ./$start_script
        cd - > /dev/null
        echo -e "${GREEN}✓ $tool_name 启动完成${NC}"
    else
        echo -e "${YELLOW}⚠ 跳过 $tool_name (目录或脚本不存在)${NC}"
    fi
}

# 启动 AI Model Compare
start_tool "AI模型对比" "ai-model-compare" "restart.sh"

# 启动 Excel Parse Tools
start_tool "Excel解析工具" "excelParseTools" "start.sh"

echo ""
echo -e "${GREEN}=========================================="
echo -e "         所有工具启动完成！"
echo -e "==========================================${NC}"
echo ""
echo "访问地址："
echo -e "  ${GREEN}http://localhost:8000/ai-model-compare/ui${NC}  - AI模型对比"
echo -e "  ${GREEN}http://localhost:5001/excel-tools/${NC}         - Excel解析工具"
echo ""
echo "管理命令："
echo "  查看所有进程: ps aux | grep -E '(uvicorn|flask|python.*run.py)'"
echo "  停止所有服务: ./stop-all.sh"
echo ""

