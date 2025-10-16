#!/bin/bash
# 远程服务器 Nginx 配置脚本

set -e

REMOTE_HOST="192.168.51.67"
REMOTE_USER="admin"

echo "╔════════════════════════════════════════════════╗"
echo "║   配置远程 Nginx                               ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 提示用户输入密码（只需输入一次）
read -sp "请输入远程服务器密码: " REMOTE_PASS
echo ""
echo ""

# 上传 nginx 配置文件
echo "【步骤 1/5】上传 Nginx 配置文件..."
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no \
  aistarfish-tools.nginx.conf \
  "${REMOTE_USER}@${REMOTE_HOST}:/tmp/"
echo "✓ 配置文件已上传"
echo ""

# 创建远程执行脚本
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'REMOTE_SCRIPT'
#!/bin/bash
set -e

echo "【步骤 2/5】配置 Hosts 文件..."
# 备份原有 hosts
if [ -f /etc/hosts ]; then
    echo "$SUDO_PASS" | sudo -S cp /etc/hosts /etc/hosts.bak.$(date +%Y%m%d-%H%M%S)
fi

# 清空并写入新的 hosts 配置
echo "127.0.0.1 tools.aistarfish.com" | sudo tee /etc/hosts > /dev/null

echo "✓ Hosts 配置已更新"
echo ""

echo "【步骤 3/5】安装 Nginx..."
sudo yum install -y nginx 2>&1 | grep -E "(Installing|Complete|already installed)" || true
echo "✓ Nginx 已安装"
echo ""

echo "【步骤 4/5】配置 Nginx..."
# 备份原有配置
if [ -f /etc/nginx/conf.d/aistarfish-tools.conf ]; then
    sudo cp /etc/nginx/conf.d/aistarfish-tools.conf /etc/nginx/conf.d/aistarfish-tools.conf.bak.$(date +%Y%m%d-%H%M%S)
fi

# 复制新配置
sudo cp /tmp/aistarfish-tools.nginx.conf /etc/nginx/conf.d/aistarfish-tools.conf

# 测试配置
echo "测试 Nginx 配置..."
sudo nginx -t

echo "✓ Nginx 配置已更新"
echo ""

echo "【步骤 5/5】启动/重启 Nginx..."
# 确保 nginx 服务已启用并启动
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "✓ Nginx 已启动"
echo ""

# 检查状态
echo "Nginx 状态:"
sudo systemctl status nginx --no-pager | head -10

echo ""
echo "监听端口:"
sudo netstat -tunlp | grep nginx || true

REMOTE_SCRIPT

# 上传并执行脚本
echo "【远程步骤 2-5】上传并执行配置脚本..."
sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no "$TEMP_SCRIPT" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/setup_nginx.sh"

echo "执行远程配置..."
sshpass -p "$REMOTE_PASS" ssh -tt \
  -o StrictHostKeyChecking=no \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=10 \
  "${REMOTE_USER}@${REMOTE_HOST}" << EOF
export SUDO_PASS="$REMOTE_PASS"
chmod +x /tmp/setup_nginx.sh
bash /tmp/setup_nginx.sh
rm -f /tmp/setup_nginx.sh /tmp/aistarfish-tools.nginx.conf
exit
EOF

# 清理临时文件
rm -f "$TEMP_SCRIPT"

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║            ✅ Nginx 配置完成！                 ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "🌐 访问地址："
echo "   ├─ AI模型对比: http://192.168.51.67/ai-model-compare/ui"
echo "   └─ Excel解析:  http://192.168.51.67/excel-tools/"
echo ""
echo "📋 管理命令："
echo "   查看状态: ssh admin@192.168.51.67 'sudo systemctl status nginx'"
echo "   重启服务: ssh admin@192.168.51.67 'sudo systemctl restart nginx'"
echo "   查看日志: ssh admin@192.168.51.67 'sudo tail -f /var/log/nginx/error.log'"
echo ""

