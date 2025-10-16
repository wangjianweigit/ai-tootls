#!/bin/bash
set -e

echo "=== Excel解析工具启动脚本 ==="

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查Python
echo -e "${YELLOW}检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python 3${NC}"
    exit 1
fi

# 检查并创建虚拟环境（使用 Python 3.11）
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    # 优先使用 python3.11，如果不存在则使用 python3
    if command -v python3.11 &> /dev/null; then
        python3.11 -m venv .venv
    else
        python3 -m venv .venv
    fi
    echo -e "${GREEN}虚拟环境创建成功${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source .venv/bin/activate

# 升级 pip
echo -e "${YELLOW}升级 pip...${NC}"
pip install --upgrade pip -q

# 配置国内镜像源（清华源）
echo -e "${YELLOW}配置 pip 镜像源...${NC}"
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

# 检查并安装依赖
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}安装依赖包...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}依赖包已安装${NC}"
fi

# 初始化目录
python3 -c "from config import Config; Config.init_directories()"

# 检查端口
PORT=5001
echo -e "${YELLOW}检查端口 $PORT...${NC}"
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}端口 $PORT 已被占用，尝试停止旧进程...${NC}"
    PID=$(lsof -t -i:$PORT)
    kill $PID 2>/dev/null || true
    sleep 2
fi

# 启动服务
echo -e "${YELLOW}启动Excel解析工具...${NC}"
nohup python3 run.py > excel_parser.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > .excel_parser.pid

sleep 2

# 检查服务状态
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 启动成功！${NC}"
    echo ""
    echo "=== 服务信息 ==="
    echo -e "  PID: ${GREEN}$NEW_PID${NC}"
    echo -e "  端口: ${GREEN}$PORT${NC}"
    echo ""
    echo "=== 访问地址 ==="
    echo -e "  Excel解析: ${GREEN}http://localhost:$PORT/excel-tools/${NC}"
    echo -e "  日志管理: ${GREEN}http://localhost:$PORT/excel-tools/logs${NC}"
    echo ""
    echo "=== 管理命令 ==="
    echo "  查看日志: tail -f excel_parser.log"
    echo "  停止服务: kill $NEW_PID"
    echo ""
else
    echo -e "${RED}✗ 启动失败${NC}"
    echo "查看日志: cat excel_parser.log"
    exit 1
fi

