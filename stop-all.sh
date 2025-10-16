#!/bin/bash

echo "=========================================="
echo "      海心AI工具集 - 统一停止脚本"
echo "=========================================="

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 停止 AI Model Compare
if [ -f "ai-model-compare/.uvicorn.pid" ]; then
    PID=$(cat ai-model-compare/.uvicorn.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}停止 AI模型对比 (PID: $PID)...${NC}"
        kill $PID
        echo -e "${GREEN}✓ 已停止${NC}"
    fi
fi

# 停止 Excel Parse Tools
if [ -f "excelParseTools/.excel_parser.pid" ]; then
    PID=$(cat excelParseTools/.excel_parser.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}停止 Excel解析工具 (PID: $PID)...${NC}"
        kill $PID
        echo -e "${GREEN}✓ 已停止${NC}"
    fi
fi

# 清理可能残留的进程
echo -e "${YELLOW}检查残留进程...${NC}"
pkill -f "uvicorn app.main:app" 2>/dev/null && echo -e "${GREEN}✓ 清理 uvicorn 进程${NC}" || true
pkill -f "python.*run.py" 2>/dev/null && echo -e "${GREEN}✓ 清理 Excel Parser 进程${NC}" || true

echo ""
echo -e "${GREEN}所有服务已停止！${NC}"

