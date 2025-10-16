#!/bin/bash
# 服务状态检查脚本

REMOTE_HOST="192.168.51.67"
REMOTE_USER="admin"

echo "╔════════════════════════════════════════════════╗"
echo "║   检查远程服务状态                             ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 提示用户输入密码
read -sp "请输入远程服务器密码: " REMOTE_PASS
echo ""
echo ""

echo "【1/5】检查 Nginx 状态..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" << 'EOF'
sudo systemctl status nginx | head -5
echo ""
EOF

echo "【2/5】检查 Docker 容器状态..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" << 'EOF'
echo "Docker 容器列表："
sudo docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
EOF

echo "【3/5】检查端口监听状态..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" << 'EOF'
echo "监听的端口："
sudo netstat -tunlp | grep -E ":(80|8000|5001)" || echo "⚠️  端口 80/8000/5001 未监听"
echo ""
EOF

echo "【4/5】检查 Hosts 配置..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" << 'EOF'
echo "当前 hosts 文件内容："
cat /etc/hosts
echo ""
EOF

echo "【5/5】检查 Nginx 配置..."
sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" << 'EOF'
echo "Nginx 配置的域名："
sudo grep -E "server_name" /etc/nginx/conf.d/aistarfish-tools.conf || echo "⚠️  配置文件不存在"
echo ""
EOF

echo "╔════════════════════════════════════════════════╗"
echo "║            ✅ 检查完成                         ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "📋 诊断建议："
echo "   1. 如果 Docker 容器未运行，执行: ./remote-docker-deploy.sh"
echo "   2. 如果域名不匹配，需要统一域名配置"
echo "   3. 如果端口未监听，检查容器日志"
echo ""

