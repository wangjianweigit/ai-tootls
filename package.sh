#!/bin/bash
# 海心AI工具集 - 打包脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_NAME="haixin-tools-$(date +%Y%m%d-%H%M%S).tar.gz"
TEMP_DIR="/tmp/haixin-tools-package"

echo "╔════════════════════════════════════════════════╗"
echo "║        海心AI工具集 - 代码打包                   ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 清理临时目录
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR/haixin-tools"

echo "📦 开始打包..."
echo ""

# 复制文件
echo "✓ 复制 AI模型对比..."
rsync -av --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='.venv' \
          --exclude='app.log' \
          --exclude='.uvicorn.pid' \
          --exclude='data/*.sqlite3' \
          --exclude='models-export.json' \
          "$SCRIPT_DIR/ai-model-compare/" \
          "$TEMP_DIR/haixin-tools/ai-model-compare/"

echo "✓ 复制 Excel解析工具..."
if [ -d "$SCRIPT_DIR/excelParseTools" ]; then
    rsync -av --exclude='__pycache__' \
              --exclude='*.pyc' \
              --exclude='.venv' \
              --exclude='logs/' \
              --exclude='excel_parser_data/temp/' \
              --exclude='*.log' \
              "$SCRIPT_DIR/excelParseTools/" \
              "$TEMP_DIR/haixin-tools/excelParseTools/"
else
    echo "  ⚠️  excelParseTools 目录不存在，跳过"
    mkdir -p "$TEMP_DIR/haixin-tools/excelParseTools"
fi

echo "✓ 复制配置文件..."
# 注意：只复制以下安全文件，不包含敏感的部署脚本
# 已排除：package.sh, deploy-docker.sh, remote-docker-deploy.sh (包含服务器密码)
cp "$SCRIPT_DIR/tools.json" "$TEMP_DIR/haixin-tools/"
cp "$SCRIPT_DIR/start-all.sh" "$TEMP_DIR/haixin-tools/"
cp "$SCRIPT_DIR/stop-all.sh" "$TEMP_DIR/haixin-tools/"
cp "$SCRIPT_DIR/aistarfish-tools.nginx.conf" "$TEMP_DIR/haixin-tools/"
cp "$SCRIPT_DIR/README.md" "$TEMP_DIR/haixin-tools/"

echo "✓ 创建必要目录..."
mkdir -p "$TEMP_DIR/haixin-tools/ai-model-compare/data"
mkdir -p "$TEMP_DIR/haixin-tools/excelParseTools/logs"
mkdir -p "$TEMP_DIR/haixin-tools/excelParseTools/excel_parser_data/temp"
mkdir -p "$TEMP_DIR/haixin-tools/excelParseTools/excel_parser_data/imports"
mkdir -p "$TEMP_DIR/haixin-tools/excelParseTools/excel_parser_data/exports"

echo "✓ 创建安装脚本..."
cat > "$TEMP_DIR/haixin-tools/install.sh" << 'INSTALL_SCRIPT'
#!/bin/bash
# 海心AI工具集 - 远程安装脚本

set -e

echo "╔════════════════════════════════════════════════╗"
echo "║      海心AI工具集 - 远程服务器安装              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

INSTALL_DIR="/opt/haixin-tools"

# 检查是否为root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用root权限运行此脚本"
    echo "   sudo ./install.sh"
    exit 1
fi

echo "【1】安装系统依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx

echo ""
echo "【2】创建安装目录"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
mkdir -p "$INSTALL_DIR"
cp -r ./* "$INSTALL_DIR/"
cd "$INSTALL_DIR"

echo ""
echo "【3】安装AI模型对比依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd "$INSTALL_DIR/ai-model-compare"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate

echo ""
echo "【4】安装Excel解析工具依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd "$INSTALL_DIR/excelParseTools"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate

echo ""
echo "【5】配置Nginx"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cp "$INSTALL_DIR/aistarfish-tools.nginx.conf" /etc/nginx/sites-available/aistarfish-tools.conf
ln -sf /etc/nginx/sites-available/aistarfish-tools.conf /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo ""
echo "【6】创建systemd服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# AI模型对比服务
cat > /etc/systemd/system/ai-model-compare.service << 'SERVICE1'
[Unit]
Description=AI Model Compare Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/haixin-tools/ai-model-compare
ExecStart=/opt/haixin-tools/ai-model-compare/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE1

# Excel解析工具服务
cat > /etc/systemd/system/excel-parse-tools.service << 'SERVICE2'
[Unit]
Description=Excel Parse Tools Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/haixin-tools/excelParseTools
ExecStart=/opt/haixin-tools/excelParseTools/.venv/bin/python web_interface.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE2

systemctl daemon-reload
systemctl enable ai-model-compare
systemctl enable excel-parse-tools
systemctl start ai-model-compare
systemctl start excel-parse-tools

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║              安装完成！                        ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "服务状态："
systemctl status ai-model-compare --no-pager
systemctl status excel-parse-tools --no-pager
echo ""
echo "访问地址："
echo "  http://服务器IP/ai-model-compare/ui"
echo "  http://服务器IP/excel-tools/"
echo ""
echo "域名配置："
echo "  请将 aistarfish.tools.com 解析到服务器IP"
echo "  然后访问 http://aistarfish.tools.com/"
echo ""
INSTALL_SCRIPT

chmod +x "$TEMP_DIR/haixin-tools/install.sh"
chmod +x "$TEMP_DIR/haixin-tools/start-all.sh"
chmod +x "$TEMP_DIR/haixin-tools/stop-all.sh"

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

# 远程服务器配置
REMOTE_HOST="192.168.51.67"
REMOTE_USER="admin"
REMOTE_DIR="/home/admin"

# 询问是否上传
echo "═══════════════════════════════════════════════════"
read -p "是否上传到远程服务器 ${REMOTE_USER}@${REMOTE_HOST}? (y/n): " -n 1 -r
echo ""
echo "═══════════════════════════════════════════════════"

# 如果用户选择上传，提示输入密码
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "请输入远程服务器密码："
    read -s REMOTE_PASS
    echo ""
fi

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "【上传到远程服务器】"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 检查是否安装了 sshpass
    if ! command -v sshpass &> /dev/null; then
        echo "⚠️  未安装 sshpass，使用交互式上传（需要手动输入密码）"
        echo ""
        
        # 使用 scp 上传（需要手动输入密码）
        scp "$SCRIPT_DIR/$PACKAGE_NAME" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ 上传成功！"
            echo ""
            echo "远程路径: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/$PACKAGE_NAME"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "【在远程服务器上执行以下命令】"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "  cd ${REMOTE_DIR}"
            echo "  tar -xzf $PACKAGE_NAME"
            echo "  cd haixin-tools"
            echo "  ./start-all.sh"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "【或者一键执行】"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "  ssh ${REMOTE_USER}@${REMOTE_HOST}"
            echo ""
            echo "  cd ${REMOTE_DIR} && tar -xzf $PACKAGE_NAME && cd haixin-tools && ./start-all.sh"
            echo ""
        else
            echo "❌ 上传失败"
        fi
    else
        echo "✓ 使用 sshpass 自动上传..."
        
        # 使用 sshpass 自动上传
        sshpass -p "$REMOTE_PASS" scp "$SCRIPT_DIR/$PACKAGE_NAME" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ 上传成功！"
            echo ""
            
            # 询问是否自动解压和启动
            read -p "是否自动解压并启动服务? (y/n): " -n 1 -r
            echo ""
            
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo ""
                echo "【自动部署】"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                
                sshpass -p "$REMOTE_PASS" ssh "${REMOTE_USER}@${REMOTE_HOST}" << REMOTE_COMMANDS
cd ${REMOTE_DIR}
tar -xzf $PACKAGE_NAME
cd haixin-tools
./start-all.sh
REMOTE_COMMANDS
                
                echo ""
                echo "✅ 部署完成！"
                echo ""
                echo "访问地址："
                echo "  🌐 http://${REMOTE_HOST}:8000/ai-model-compare/ui  - AI模型对比"
                echo "  🌐 http://${REMOTE_HOST}:5001/excel-tools/         - Excel解析工具"
                echo ""
            else
                echo ""
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo "【在远程服务器上执行以下命令】"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo ""
                echo "  cd ${REMOTE_DIR}"
                echo "  tar -xzf $PACKAGE_NAME"
                echo "  cd haixin-tools"
                echo "  ./start-all.sh"
                echo ""
            fi
        else
            echo "❌ 上传失败"
        fi
    fi
else
    echo ""
    echo "手动部署步骤："
    echo "  1. 上传: scp $PACKAGE_NAME ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"
    echo "  2. SSH登录: ssh ${REMOTE_USER}@${REMOTE_HOST}"
    echo "  3. 解压: cd ${REMOTE_DIR} && tar -xzf $PACKAGE_NAME"
    echo "  4. 启动: cd haixin-tools && ./start-all.sh"
    echo ""
fi

# 清理
rm -rf "$TEMP_DIR"
