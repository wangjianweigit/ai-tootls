#!/bin/bash
set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== AI Model Compare 快速重启 ==="

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查端口
PORT=8000

# 停止旧进程
echo -e "${YELLOW}停止旧进程...${NC}"
if [ -f .uvicorn.pid ]; then
    OLD_PID=$(cat .uvicorn.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        kill $OLD_PID
        echo -e "${GREEN}已停止进程 $OLD_PID${NC}"
        sleep 2
    else
        echo -e "${YELLOW}进程 $OLD_PID 不存在${NC}"
    fi
fi

# 检查端口是否还被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}端口 $PORT 仍被占用，强制终止...${NC}"
    PID=$(lsof -t -i:$PORT)
    kill -9 $PID 2>/dev/null || true
    sleep 1
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

# 启动服务
echo -e "${YELLOW}启动新进程...${NC}"
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT > app.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > .uvicorn.pid

# 等待服务启动
sleep 3

# 检查服务状态
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 重启成功！${NC}"
    echo ""
    echo "=== 服务信息 ==="
    echo -e "  PID: ${GREEN}$NEW_PID${NC}"
    echo -e "  端口: ${GREEN}$PORT${NC}"
    echo ""
    echo "=== 访问地址 ==="
    echo -e "  模型对比页: ${GREEN}http://localhost:$PORT/ai-model-compare/ui${NC}"
    echo -e "  模型管理页: ${GREEN}http://localhost:$PORT/ai-model-compare/models-ui${NC}"
    echo -e "  对比历史页: ${GREEN}http://localhost:$PORT/ai-model-compare/history-ui${NC}"
    echo ""
    echo "=== 管理命令 ==="
    echo "  查看日志: tail -f app.log"
    echo "  停止服务: kill $NEW_PID"
    echo "  再次重启: ./restart.sh"
    echo ""
else
    echo -e "${RED}✗ 启动失败${NC}"
    echo "查看日志: tail -20 app.log"
    cat app.log | tail -20
    exit 1
fi

