#!/bin/bash
# 远程 Docker 部署脚本

set -e

# 配置
REMOTE_HOST="192.168.51.67"
REMOTE_USER="admin"
REMOTE_DIR="/home/admin"

echo "╔════════════════════════════════════════════════╗"
echo "║   远程 Docker 部署                             ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 提示用户输入密码（只需输入一次）
read -sp "请输入远程服务器密码: " REMOTE_PASS
echo ""
echo ""

# 创建远程执行脚本
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EXEC_SCRIPT'
#!/bin/bash
set -e

cd /home/admin

# 查找最新的打包文件
LATEST_PACKAGE=$(ls -t haixin-tools-*.tar.gz 2>/dev/null | head -1)

if [ -n "$LATEST_PACKAGE" ]; then
    echo "找到新包: $LATEST_PACKAGE"
    echo "解压中..."
    
    # 备份数据目录（保留用户数据）
    BACKUP_DATA=""
    if [ -d haixin-tools/ai-model-compare/data ]; then
        BACKUP_DATA="/tmp/ai-model-compare-data-backup-$$"
        echo "备份数据目录..."
        cp -r haixin-tools/ai-model-compare/data "$BACKUP_DATA"
    fi
    
    BACKUP_EXCEL_DATA=""
    if [ -d haixin-tools/excelParseTools/excel_parser_data ]; then
        BACKUP_EXCEL_DATA="/tmp/excel-parser-data-backup-$$"
        echo "备份Excel数据目录..."
        cp -r haixin-tools/excelParseTools/excel_parser_data "$BACKUP_EXCEL_DATA"
    fi
    
    BACKUP_EXCEL_LOGS=""
    if [ -d haixin-tools/excelParseTools/logs ]; then
        BACKUP_EXCEL_LOGS="/tmp/excel-parser-logs-backup-$$"
        echo "备份Excel日志目录..."
        cp -r haixin-tools/excelParseTools/logs "$BACKUP_EXCEL_LOGS"
    fi
    
    # 备份旧版本代码
    if [ -d haixin-tools ]; then
        mv haixin-tools haixin-tools.bak.$(date +%Y%m%d-%H%M%S) 2>/dev/null || rm -rf haixin-tools
    fi
    
    # 解压新版本
    tar -xzf "$LATEST_PACKAGE"
    
    # 恢复数据目录
    if [ -n "$BACKUP_DATA" ] && [ -d "$BACKUP_DATA" ]; then
        echo "恢复AI模型对比数据..."
        rm -rf haixin-tools/ai-model-compare/data
        mv "$BACKUP_DATA" haixin-tools/ai-model-compare/data
    fi
    
    if [ -n "$BACKUP_EXCEL_DATA" ] && [ -d "$BACKUP_EXCEL_DATA" ]; then
        echo "恢复Excel数据..."
        rm -rf haixin-tools/excelParseTools/excel_parser_data
        mv "$BACKUP_EXCEL_DATA" haixin-tools/excelParseTools/excel_parser_data
    fi
    
    if [ -n "$BACKUP_EXCEL_LOGS" ] && [ -d "$BACKUP_EXCEL_LOGS" ]; then
        echo "恢复Excel日志..."
        rm -rf haixin-tools/excelParseTools/logs
        mv "$BACKUP_EXCEL_LOGS" haixin-tools/excelParseTools/logs
    fi
    
    echo "✓ 数据恢复完成"
fi

cd /home/admin/haixin-tools

echo "╔════════════════════════════════════════════════╗"
echo "║   海心AI工具集 - Docker 部署                     ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}【步骤 1/4】拉取基础镜像${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$SUDO_PASS" | sudo -S docker pull registry.cn-shanghai.aliyuncs.com/hxzh_dev/hxzh-python:3.11
echo -e "${GREEN}✓ 镜像已拉取${NC}"
echo ""

echo -e "${BLUE}【步骤 2/4】构建应用镜像${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "构建 AI 模型对比镜像（可能需要几分钟）..."
cd ai-model-compare
sudo docker build -t haixin-ai-model-compare:latest . 2>&1 | grep -E "(Step|Successfully|ERROR)" || true
cd ..

echo "构建 Excel 解析工具镜像（可能需要几分钟）..."
cd excelParseTools
sudo docker build -t haixin-excel-tools:latest . 2>&1 | grep -E "(Step|Successfully|ERROR)" || true
cd ..
echo -e "${GREEN}✓ 镜像构建完成${NC}"
echo ""

echo -e "${BLUE}【步骤 3/4】停止旧容器${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo docker stop ai-model-compare 2>/dev/null || true
sudo docker rm ai-model-compare 2>/dev/null || true
sudo docker stop excel-parse-tools 2>/dev/null || true
sudo docker rm excel-parse-tools 2>/dev/null || true
echo -e "${GREEN}✓ 旧容器已停止${NC}"
echo ""

echo -e "${BLUE}【步骤 4/4】启动新容器${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 启动 AI 模型对比
# 检查镜像是否构建成功
if sudo docker images | grep -q haixin-ai-model-compare; then
    echo "启动 AI 模型对比..."
    sudo docker run -d \
      --name ai-model-compare \
      -p 8000:8000 \
      -v /home/admin/haixin-tools/ai-model-compare/data:/app/data \
      -v /home/admin/haixin-tools/ai-model-compare/config:/app/config \
      -e TZ=Asia/Shanghai \
      --restart unless-stopped \
      haixin-ai-model-compare:latest
    echo -e "${GREEN}✓ AI 模型对比已启动${NC}"
else
    echo -e "${YELLOW}⚠️  AI 模型对比镜像构建失败，跳过启动${NC}"
fi

# 启动 Excel 解析工具
if sudo docker images | grep -q haixin-excel-tools; then
    echo "启动 Excel 解析工具..."
    sudo docker run -d \
      --name excel-parse-tools \
      -p 5001:5001 \
      -v /home/admin/haixin-tools/excelParseTools/logs:/app/logs \
      -v /home/admin/haixin-tools/excelParseTools/excel_parser_data:/app/excel_parser_data \
      -e TZ=Asia/Shanghai \
      --restart unless-stopped \
      haixin-excel-tools:latest
    echo -e "${GREEN}✓ Excel 解析工具已启动${NC}"
else
    echo -e "${YELLOW}⚠️  Excel 解析工具镜像构建失败，跳过启动${NC}"
fi

echo -e "${GREEN}✓ 容器已启动${NC}"
echo ""

# 等待服务启动
echo "等待服务初始化..."
sleep 3

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║            🎉 部署完成！                       ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "🌐 访问地址："
echo "   ├─ AI模型对比: http://192.168.51.67:8000/ai-model-compare/ui"
echo "   └─ Excel解析:  http://192.168.51.67:5001/excel-tools/"
echo ""
echo "🔧 管理命令："
echo "   查看容器: sudo docker ps"
echo "   查看日志: sudo docker logs -f ai-model-compare"
echo "   停止服务: sudo docker stop ai-model-compare excel-parse-tools"
echo ""
EXEC_SCRIPT

# 查找最新的打包文件
LATEST_PACKAGE=$(ls -t haixin-tools-*.tar.gz 2>/dev/null | head -1)
if [ -z "$LATEST_PACKAGE" ]; then
    echo "❌ 错误：未找到打包文件"
    echo "请先运行: ./package.sh"
    exit 1
fi

echo "📦 找到最新包: $LATEST_PACKAGE"
echo ""

# 上传打包文件
echo "上传打包文件到远程服务器..."
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no "$LATEST_PACKAGE" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
echo "✓ 上传完成"
echo ""

# 上传并执行脚本
echo "上传部署脚本..."
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no "$TEMP_SCRIPT" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/docker_deploy.sh"

echo "执行部署..."
sshpass -p "$REMOTE_PASS" ssh -tt \
  -o StrictHostKeyChecking=no \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=10 \
  "${REMOTE_USER}@${REMOTE_HOST}" << EOF
export SUDO_PASS="$REMOTE_PASS"
chmod +x /tmp/docker_deploy.sh
bash /tmp/docker_deploy.sh
rm -f /tmp/docker_deploy.sh
exit
EOF

# 清理临时文件
rm -f "$TEMP_SCRIPT"

echo ""
echo "✅ 部署完成！"

