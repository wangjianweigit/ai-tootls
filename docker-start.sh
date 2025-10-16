#!/bin/bash
# Docker 方式启动所有服务

set -e

echo "╔════════════════════════════════════════════════╗"
echo "║   海心AI工具集 - Docker 启动脚本                 ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 切换到脚本所在目录
cd "$(dirname "$0")"

echo -e "${BLUE}【步骤 1/3】检查 Docker 环境${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  未找到 Docker，请先安装 Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  未找到 docker-compose，请先安装${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker 环境检查通过${NC}"
echo ""

echo -e "${BLUE}【步骤 2/3】停止旧容器${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ 旧容器已停止${NC}"
echo ""

echo -e "${BLUE}【步骤 3/3】构建并启动服务${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}正在构建镜像...${NC}"
sudo docker-compose build

echo ""
echo -e "${YELLOW}正在启动容器...${NC}"
sudo docker-compose up -d

echo ""
echo -e "${GREEN}✓ 服务启动成功${NC}"
echo ""

# 等待服务启动
echo "等待服务初始化..."
sleep 5

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║            🎉 部署完成！                       ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "🌐 访问地址："
echo "   ├─ AI模型对比: http://localhost:8000/ai-model-compare/ui"
echo "   │              http://localhost:8000/ai-model-compare/models-ui"
echo "   │              http://localhost:8000/ai-model-compare/history-ui"
echo "   │"
echo "   └─ Excel解析:  http://localhost:5001/excel-tools/"
echo "                  http://localhost:5001/excel-tools/logs"
echo ""
echo "🔧 管理命令："
echo "   查看容器状态: docker-compose ps"
echo "   查看日志:     docker-compose logs -f"
echo "   停止服务:     docker-compose down"
echo "   重启服务:     docker-compose restart"
echo ""

