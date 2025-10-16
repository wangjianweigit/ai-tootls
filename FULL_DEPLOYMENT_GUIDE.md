# 🚀 海心AI工具集 - 完整部署指南

**最后更新**: 2025年10月15日  

---

## 📋 目录

1. [系统架构](#系统架构)
2. [快速开始](#快速开始)
3. [详细步骤](#详细步骤)
4. [访问地址](#访问地址)
5. [管理命令](#管理命令)
6. [故障排查](#故障排查)

---

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│  客户端浏览器                                            │
└────────────────┬─────────────────────────────────────────┘
                 │ HTTP/HTTPS
                 ▼
┌──────────────────────────────────────────────────────────┐
│  Nginx 反向代理 (端口 80/443)                            │
│  ├─ /ai-model-compare/  → 127.0.0.1:8000               │
│  └─ /excel-tools/       → 127.0.0.1:5001               │
└────────────────┬─────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Docker      │  │  Docker      │
│  Container   │  │  Container   │
│              │  │              │
│  ai-model-   │  │  excel-      │
│  compare     │  │  parse-tools │
│              │  │              │
│  端口: 8000  │  │  端口: 5001  │
└──────────────┘  └──────────────┘
```

---

## 快速开始

### 一键部署

```bash
# 1. 完整部署（打包 + 上传 + Docker 部署 + Nginx 配置）
./deploy-docker.sh && ./setup-nginx.sh

# 2. 访问服务
open http://192.168.51.67/ai-model-compare/ui
```

---

## 详细步骤

### 步骤 1: 打包项目

```bash
./package.sh
```

**输出**: `haixin-tools-YYYYMMDD-HHMMSS.tar.gz`

---

### 步骤 2: Docker 部署

```bash
./deploy-docker.sh
```

**执行内容**:
1. 上传打包文件到远程服务器
2. 检查 Docker 环境
3. 停止旧容器
4. 解压并构建新镜像
5. 启动新容器

**基础镜像**: `registry.cn-shanghai.aliyuncs.com/hxzh_dev/hxzh-python:3.11`

**Dockerfile 关键配置**:

```dockerfile
# AI 模型对比
FROM registry.cn-shanghai.aliyuncs.com/hxzh_dev/hxzh-python:3.11
RUN pip install --no-cache-dir pillow python-multipart jinja2
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Excel 解析工具
FROM registry.cn-shanghai.aliyuncs.com/hxzh_dev/hxzh-python:3.11
RUN pip install --no-cache-dir openpyxl flask flask-cors
EXPOSE 5001
CMD ["python", "run.py"]
```

---

### 步骤 3: 配置 Nginx

```bash
./setup-nginx.sh
```

**执行内容**:
1. 上传 `aistarfish-tools.nginx.conf`
2. 安装 Nginx（如果未安装）
3. 复制配置到 `/etc/nginx/conf.d/`
4. 测试配置
5. 重启 Nginx

**Nginx 配置要点**:

```nginx
# 反向代理到 Docker 容器
upstream ai_model_compare {
    server 127.0.0.1:8000;
    keepalive 32;
}

upstream excel_parse_tools {
    server 127.0.0.1:5001;
    keepalive 32;
}

server {
    listen 80;
    server_name aistarfish.tools.com;
    client_max_body_size 50M;
    
    # AI 模型对比
    location /ai-model-compare/ {
        proxy_pass http://ai_model_compare/ai-model-compare/;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_read_timeout 600s;
    }
    
    # Excel 解析工具
    location /excel-tools/ {
        proxy_pass http://excel_parse_tools/excel-tools/;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_read_timeout 1200s;
    }
}
```

---

## 访问地址

### 通过 Nginx 访问（推荐）

| 服务 | 地址 |
|------|------|
| **AI 模型对比 - UI** | http://192.168.51.67/ai-model-compare/ui |
| **AI 模型对比 - 模型管理** | http://192.168.51.67/ai-model-compare/models-ui |
| **AI 模型对比 - 历史记录** | http://192.168.51.67/ai-model-compare/history-ui |
| **Excel 解析工具 - 主页** | http://192.168.51.67/excel-tools/ |
| **Excel 解析工具 - 日志** | http://192.168.51.67/excel-tools/logs |
| **健康检查** | http://192.168.51.67/health |

### 直接访问 Docker 容器

| 服务 | 地址 |
|------|------|
| AI 模型对比 | http://192.168.51.67:8000/ai-model-compare/ui |
| Excel 解析工具 | http://192.168.51.67:5001/excel-tools/ |

---

## 管理命令

### Docker 容器管理

```bash
# SSH 登录
ssh admin@192.168.51.67

# 查看容器状态
sudo docker ps

# 查看日志
sudo docker logs -f ai-model-compare
sudo docker logs -f excel-parse-tools

# 重启容器
sudo docker restart ai-model-compare excel-parse-tools

# 停止容器
sudo docker stop ai-model-compare excel-parse-tools

# 启动容器
sudo docker start ai-model-compare excel-parse-tools

# 删除容器
sudo docker rm -f ai-model-compare excel-parse-tools

# 查看镜像
sudo docker images | grep haixin
```

### Nginx 管理

```bash
# 查看状态
sudo systemctl status nginx

# 重启服务
sudo systemctl restart nginx

# 停止服务
sudo systemctl stop nginx

# 启动服务
sudo systemctl start nginx

# 测试配置
sudo nginx -t

# 查看访问日志
sudo tail -f /var/log/nginx/aistarfish-access.log

# 查看错误日志
sudo tail -f /var/log/nginx/aistarfish-error.log

# 查看配置文件
cat /etc/nginx/conf.d/aistarfish-tools.conf
```

### 本地快速管理

```bash
# 重新部署
./deploy-docker.sh

# 重新配置 Nginx
./setup-nginx.sh

# 查看远程容器状态
ssh admin@192.168.51.67 "sudo docker ps"

# 查看远程 Nginx 状态
ssh admin@192.168.51.67 "sudo systemctl status nginx"
```

---

## 故障排查

### 1. Docker 容器无法启动

**症状**: 容器状态为 `Restarting`

**排查步骤**:

```bash
# 查看容器日志
sudo docker logs --tail 50 ai-model-compare

# 常见问题：
# - 缺少依赖包 → 检查 Dockerfile
# - 端口被占用 → 检查端口占用情况
# - 配置文件错误 → 检查 .env 文件
```

**解决方案**:

```bash
# 重新构建镜像
cd /home/admin/haixin-tools/ai-model-compare
sudo docker build -t haixin-ai-model-compare:latest .

# 重新启动容器
sudo docker stop ai-model-compare
sudo docker rm ai-model-compare
sudo docker run -d \
  --name ai-model-compare \
  -p 8000:8000 \
  -v /home/admin/haixin-tools/ai-model-compare/data:/app/data \
  -v /home/admin/haixin-tools/ai-model-compare/config:/app/config \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  haixin-ai-model-compare:latest
```

---

### 2. Nginx 502 Bad Gateway

**症状**: 访问服务返回 502 错误

**排查步骤**:

```bash
# 1. 检查容器是否运行
sudo docker ps

# 2. 检查容器日志
sudo docker logs ai-model-compare

# 3. 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 4. 测试后端服务
curl http://127.0.0.1:8000/ai-model-compare/ui
curl http://127.0.0.1:5001/excel-tools/
```

**解决方案**:

```bash
# 重启容器
sudo docker restart ai-model-compare excel-parse-tools

# 重启 Nginx
sudo systemctl restart nginx

# 检查防火墙
sudo firewall-cmd --list-ports
```

---

### 3. Nginx 配置测试失败

**症状**: `nginx -t` 报错

**排查步骤**:

```bash
# 测试配置
sudo nginx -t

# 查看配置文件
cat /etc/nginx/conf.d/aistarfish-tools.conf

# 检查语法错误
sudo nginx -T | grep error
```

**解决方案**:

```bash
# 重新上传配置
./setup-nginx.sh

# 或手动修复配置
sudo vi /etc/nginx/conf.d/aistarfish-tools.conf
sudo nginx -t
sudo systemctl restart nginx
```

---

### 4. Docker 网络问题

**症状**: 容器无法访问外网或容器间无法通信

**排查步骤**:

```bash
# 检查 Docker 网络
sudo docker network ls

# 检查容器网络
sudo docker inspect ai-model-compare | grep -A 20 Networks
```

**解决方案**:

```bash
# 重启 Docker 服务
sudo systemctl restart docker

# 清理网络
sudo docker network prune
```

---

### 5. 端口被占用

**症状**: 容器启动失败，提示端口已被占用

**排查步骤**:

```bash
# 查看端口占用
sudo netstat -tunlp | grep -E '8000|5001|80'

# 查找占用进程
sudo lsof -i :8000
```

**解决方案**:

```bash
# 停止占用端口的进程
sudo kill -9 <PID>

# 或修改容器端口
sudo docker run -d --name ai-model-compare -p 8001:8000 ...
```

---

## 📚 相关文档

- `aistarfish-tools.nginx.conf` - Nginx 配置文件
- `deploy-docker.sh` - Docker 部署脚本
- `setup-nginx.sh` - Nginx 配置脚本

---

## 🔐 安全建议

1. **启用 HTTPS**
   - 申请 SSL 证书
   - 取消 `aistarfish-tools.nginx.conf` 中 HTTPS 部分的注释
   - 配置证书路径

2. **限制访问来源**
   ```nginx
   # 在 server 块中添加
   allow 192.168.0.0/16;
   deny all;
   ```

3. **添加认证**
   ```bash
   # 安装 htpasswd
   sudo yum install httpd-tools
   
   # 创建密码文件
   sudo htpasswd -c /etc/nginx/.htpasswd admin
   
   # 在 location 块中添加
   auth_basic "Restricted";
   auth_basic_user_file /etc/nginx/.htpasswd;
   ```

4. **配置防火墙**
   ```bash
   sudo firewall-cmd --permanent --add-service=http
   sudo firewall-cmd --permanent --add-service=https
   sudo firewall-cmd --reload
   ```

---

## 🎯 性能优化

1. **Nginx 优化**
   ```nginx
   worker_processes auto;
   worker_connections 1024;
   
   # 启用 gzip 压缩
   gzip on;
   gzip_types text/plain text/css application/json application/javascript;
   
   # 静态文件缓存
   location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
       expires 7d;
       add_header Cache-Control "public, immutable";
   }
   ```

2. **Docker 资源限制**
   ```bash
   docker run -d \
     --memory="512m" \
     --cpus="1.0" \
     ...
   ```

---

**部署团队**: DevOps  
**维护状态**: 活跃维护  
**支持联系**: admin@aistarfish.tools.com

