#!/bin/bash
# Docker 方式停止所有服务

echo "╔════════════════════════════════════════════════╗"
echo "║   海心AI工具集 - Docker 停止脚本                 ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}正在停止所有容器...${NC}"
sudo docker-compose down

echo ""
echo -e "${GREEN}✓ 所有容器已停止${NC}"
echo ""

