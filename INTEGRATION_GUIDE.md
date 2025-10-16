# 海心AI工具集 - 新工具接入指南

> 📘 本指南面向开发者，介绍如何将新工具接入到海心工具集平台

## 📋 目录

- [快速开始](#快速开始)
- [完整开发流程](#完整开发流程)
- [配置说明](#配置说明)
- [开发规范](#开发规范)
- [集成步骤](#集成步骤)
- [部署流程](#部署流程)
- [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 平台架构

海心工具集采用**统一导航栏 + 独立工具**的架构：

```
haixin-tools/
├── tools.json              # 全局工具配置
├── start-all.sh           # 统一启动脚本
├── stop-all.sh            # 统一停止脚本
├── ai-model-compare/      # 示例工具1：AI模型对比
│   ├── app/
│   ├── templates/
│   ├── static/
│   └── restart.sh
└── excelParseTools/       # 示例工具2：Excel解析
    ├── templates/
    ├── run.py
    └── start.sh
```

### 核心特性

✅ **统一导航栏** - 所有工具共享同一个导航栏，用户体验一致  
✅ **独立服务** - 每个工具独立运行，互不影响  
✅ **动态配置** - 通过 `tools.json` 自动发现和注册工具  
✅ **Docker 支持** - 支持 Docker 容器化部署

---

## 🔄 完整开发流程

> 📖 本章节介绍从零开始开发新工具到生产部署的完整流程

### 流程概览

```
1. 环境准备 → 2. 拉取代码 → 3. 本地开发 → 4. 测试验证 → 5. 提交代码 → 6. 打包发布 → 7. 生产部署
```

---

### 步骤 1️⃣：环境准备

#### 1.1 安装必要软件

**开发环境（Mac/Linux）**：

```bash
# 1. 安装 Python 3.11+
python3.11 --version

# 2. 安装 Git
git --version

# 3. 安装 Docker（可选，用于本地容器化测试）
docker --version
docker-compose --version

# 4. 安装 sshpass（用于远程部署）
# macOS
brew install hudochenkov/sshpass/sshpass

# Linux
sudo apt-get install sshpass  # Ubuntu/Debian
sudo yum install sshpass      # CentOS/RHEL
```

#### 1.2 配置 Git 用户信息

```bash
# 配置用户名和邮箱
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 验证配置
git config --list | grep user
```

#### 1.3 配置 SSH 密钥（推荐）

```bash
# 生成 SSH 密钥
ssh-keygen -t rsa -b 4096 -C "your.email@example.com"

# 将公钥添加到 Gitee
cat ~/.ssh/id_rsa.pub
# 复制输出内容，添加到 Gitee: 设置 → SSH公钥

# 测试连接
ssh -T git@gitee.com
```

---

### 步骤 2️⃣：拉取代码到本地

#### 2.1 克隆仓库

```bash
# 方式 1：使用 HTTPS（需要输入密码）
git clone https://gitee.com/aistarfish/ai-scene-tool.git

# 方式 2：使用 SSH（推荐，配置密钥后免密）
git clone git@gitee.com:aistarfish/ai-scene-tool.git

# 进入项目目录
cd ai-scene-tool
```

#### 2.2 查看项目结构

```bash
# 查看项目文件
ls -la

# 查看分支
git branch -a

# 查看最近提交
git log --oneline -10
```

#### 2.3 创建开发分支（推荐）

```bash
# 创建并切换到新分支
git checkout -b feature/your-new-tool

# 或者先创建后切换
git branch feature/your-new-tool
git checkout feature/your-new-tool
```

---

### 步骤 3️⃣：本地开发

#### 3.1 创建工具目录

```bash
# 创建新工具目录
mkdir your-tool
cd your-tool

# 创建基本结构
mkdir -p app templates static data logs
touch requirements.txt start.sh Dockerfile README.md
```

#### 3.2 开发工具代码

**创建 FastAPI 应用示例**：

```python
# your-tool/app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 健康检查
@app.get("/your-tool/health")
async def health():
    return {"status": "healthy"}

# 主页面
@app.get("/your-tool/ui")
async def ui(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tool_name": "Your Tool"
    })
```

**创建依赖文件**：

```bash
# your-tool/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2
python-multipart==0.0.6
```

**创建启动脚本**：

```bash
# your-tool/start.sh
#!/bin/bash

cd "$(dirname "$0")"

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3.11 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt -q

# 启动服务
echo "启动服务..."
PORT=8080  # 修改为你的端口
uvicorn app.main:app --host 0.0.0.0 --port $PORT &

# 保存进程ID
echo $! > .tool.pid
echo "✓ 服务已启动 (PID: $(cat .tool.pid), Port: $PORT)"
```

```bash
# 添加执行权限
chmod +x start.sh
```

#### 3.3 配置工具到平台

编辑根目录的 `tools.json`：

```bash
cd ..  # 回到项目根目录
nano tools.json
```

添加你的工具配置到 `tools` 数组：

```json
{
  "id": "your-tool",
  "name": "你的工具名称",
  "icon": "🔧",
  "description": "工具简短描述",
  "enabled": true,
  "owner": {
    "name": "技术团队",
    "email": "support@example.com"
  },
  "service": {
    "type": "fastapi",
    "port": 8080,
    "path_prefix": "/your-tool",
    "health_check": "/your-tool/health"
  },
  "pages": [
    {
      "key": "main",
      "title": "主页面",
      "path": "/your-tool/ui",
      "icon": "🏠"
    }
  ]
}
```

---

### 步骤 4️⃣：本地测试验证

#### 4.1 单独测试新工具

```bash
# 启动你的工具
cd your-tool
./start.sh

# 等待几秒后测试
curl http://localhost:8080/your-tool/health

# 浏览器访问
open http://localhost:8080/your-tool/ui

# 查看日志
tail -f logs/app.log
```

#### 4.2 集成测试所有工具

```bash
# 回到项目根目录
cd ..

# 启动所有工具
./start-all.sh

# 等待所有服务启动（约10-20秒）
sleep 15

# 测试各个工具
curl http://localhost:8000/ai-model-compare/health
curl http://localhost:5001/excel-tools/health  
curl http://localhost:8080/your-tool/health

# 浏览器访问测试导航栏
open http://localhost:8000/ai-model-compare/ui
```

#### 4.3 Docker 本地测试（推荐）

**创建 Dockerfile**：

```dockerfile
# your-tool/Dockerfile
FROM registry.cn-shanghai.aliyuncs.com/hxzh_dev/hxzh-python:3.11

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**更新 docker-compose.yml**：

```yaml
# 在根目录的 docker-compose.yml 中添加你的服务
your-tool:
  build:
    context: ./your-tool
    dockerfile: Dockerfile
  container_name: your-tool
  ports:
    - "8080:8080"
  volumes:
    - ./your-tool/logs:/app/logs
    - ./your-tool/data:/app/data
  environment:
    - TZ=Asia/Shanghai
  restart: unless-stopped
  networks:
    - haixin-tools
```

**启动 Docker 测试**：

```bash
# 构建并启动所有容器
./docker-start.sh

# 或者只测试你的工具
docker-compose up -d your-tool

# 查看日志
docker logs -f your-tool

# 测试访问
curl http://localhost:8080/your-tool/health
```

#### 4.4 停止测试服务

```bash
# 停止所有工具
./stop-all.sh

# 或停止 Docker
./docker-stop.sh
```

---

### 步骤 5️⃣：提交代码到 Git

#### 5.1 检查代码变更

```bash
# 查看修改的文件
git status

# 查看具体改动
git diff

# 查看暂存区改动
git diff --staged
```

#### 5.2 添加文件到暂存区

```bash
# 添加新工具目录
git add your-tool/

# 添加配置文件修改
git add tools.json

# 添加 docker-compose 修改（如果有）
git add docker-compose.yml

# 或者添加所有改动（谨慎使用）
git add .
```

#### 5.3 提交代码

```bash
# 提交到本地仓库
git commit -m "✨ 新增工具: Your Tool

功能描述：
- 实现了XXX功能
- 支持XXX操作
- 集成统一导航栏

技术栈：
- FastAPI
- Docker支持

端口：8080"
```

#### 5.4 推送到远程仓库

```bash
# 推送到远程仓库
git push origin feature/your-new-tool

# 如果是第一次推送这个分支
git push -u origin feature/your-new-tool
```

#### 5.5 创建 Pull Request（可选）

1. 访问 Gitee 仓库页面
2. 点击 "Pull Request" → "新建 Pull Request"
3. 选择源分支：`feature/your-new-tool`
4. 选择目标分支：`master`
5. 填写 PR 描述，提交审核

**或者直接合并到主分支**：

```bash
# 切换到主分支
git checkout master

# 拉取最新代码
git pull origin master

# 合并你的分支
git merge feature/your-new-tool

# 推送到远程
git push origin master
```

---

### 步骤 6️⃣：打包发布

#### 6.1 执行打包脚本

```bash
# 确保在项目根目录
cd /path/to/ai-scene-tool

# 执行打包
./package.sh
```

**打包脚本会自动**：
- ✅ 排除虚拟环境（`.venv/`、`venv/`）
- ✅ 排除日志文件（`*.log`）
- ✅ 排除数据库文件（`*.sqlite3`）
- ✅ 排除缓存文件（`__pycache__/`、`*.pyc`）
- ✅ 生成带时间戳的压缩包

**输出示例**：

```
╔════════════════════════════════════════════════╗
║        海心AI工具集 - 代码打包                   ║
╚════════════════════════════════════════════════╝

📦 开始打包...
✓ 复制 AI模型对比...
✓ 复制 Excel解析工具...
✓ 复制 Your Tool...
✓ 复制配置文件...
✓ 创建必要目录...
✓ 创建安装脚本...
✓ 打包中...

╔════════════════════════════════════════════════╗
║              打包完成！                        ║
╚════════════════════════════════════════════════╝

📦 打包文件: haixin-tools-20251016-143520.tar.gz
📊 文件大小:  25M
```

#### 6.2 验证打包文件

```bash
# 查看打包文件
ls -lh haixin-tools-*.tar.gz

# 查看压缩包内容（可选）
tar -tzf haixin-tools-*.tar.gz | head -20
```

---

### 步骤 7️⃣：生产环境部署

#### 7.1 前置检查

**部署前检查清单**：

- [ ] 代码已提交到 Git 并推送到远程
- [ ] 本地测试全部通过
- [ ] Docker 镜像构建成功
- [ ] `tools.json` 配置正确
- [ ] 端口没有冲突
- [ ] 已完成打包（`package.sh`）
- [ ] 确认服务器有足够磁盘空间
- [ ] 准备好服务器登录密码
- [ ] 已通过 VPN 连接到目标网络

#### 7.2 部署 Docker 容器

```bash
# 执行远程部署脚本
./remote-docker-deploy.sh
```

**脚本会提示输入密码**：

```
╔════════════════════════════════════════════════╗
║   远程 Docker 部署                             ║
╚════════════════════════════════════════════════╝

请输入远程服务器密码: ********
```

**自动执行流程**：

1. ✅ 查找最新打包文件
2. ✅ 上传到远程服务器（192.168.51.67）
3. ✅ 备份旧数据
   - 数据库文件
   - Excel数据目录
   - 日志文件
4. ✅ 解压新代码
5. ✅ 恢复数据文件
6. ✅ 拉取 Docker 基础镜像
7. ✅ 构建应用镜像
8. ✅ 停止旧容器
9. ✅ 启动新容器

**部署成功输出**：

```
╔════════════════════════════════════════════════╗
║            🎉 部署完成！                       ║
╚════════════════════════════════════════════════╝

🌐 访问地址：
   ├─ AI模型对比: http://192.168.51.67:8000/ai-model-compare/ui
   ├─ Excel解析:  http://192.168.51.67:5001/excel-tools/
   └─ Your Tool:  http://192.168.51.67:8080/your-tool/ui

🔧 管理命令：
   查看容器: sudo docker ps
   查看日志: sudo docker logs -f your-tool
   停止服务: sudo docker stop your-tool
```

#### 7.3 配置 Nginx 反向代理（可选）

如果需要通过域名访问：

```bash
# 执行 Nginx 配置脚本
./setup-nginx.sh
```

**脚本会提示输入密码**：

```
╔════════════════════════════════════════════════╗
║   配置远程 Nginx                               ║
╚════════════════════════════════════════════════╝

请输入远程服务器密码: ********
```

**自动执行流程**：

1. ✅ 上传 Nginx 配置文件
2. ✅ 配置远程 hosts 文件
3. ✅ 安装 Nginx（如未安装）
4. ✅ 更新 Nginx 配置
5. ✅ 测试 Nginx 配置
6. ✅ 重启 Nginx 服务

**配置成功后可通过域名访问**：

```
http://tools.aistarfish.com/ai-model-compare/ui
http://tools.aistarfish.com/excel-tools/
http://tools.aistarfish.com/your-tool/ui
```

**⚠️ 注意**：域名访问需要在本地配置 hosts：

```bash
# macOS/Linux
sudo nano /etc/hosts

# 添加以下行
192.168.51.67 tools.aistarfish.com
```

#### 7.4 验证部署

```bash
# 执行服务状态检查
./check-services.sh
```

**检查输出示例**：

```
╔════════════════════════════════════════════════╗
║   检查远程服务状态                             ║
╚════════════════════════════════════════════════╝

【1/5】检查 Nginx 状态...
● nginx.service - nginx
   Loaded: loaded
   Active: active (running)

【2/5】检查 Docker 容器状态...
NAMES                STATUS                  PORTS
ai-model-compare     Up 2 hours             0.0.0.0:8000->8000/tcp
excel-parse-tools    Up 2 hours             0.0.0.0:5001->5001/tcp
your-tool           Up 5 minutes           0.0.0.0:8080->8080/tcp

【3/5】检查端口监听状态...
tcp    0.0.0.0:80      LISTEN      nginx
tcp    0.0.0.0:8000    LISTEN      docker-proxy
tcp    0.0.0.0:5001    LISTEN      docker-proxy
tcp    0.0.0.0:8080    LISTEN      docker-proxy

【4/5】检查 Hosts 配置...
127.0.0.1 tools.aistarfish.com

【5/5】检查 Nginx 配置...
server_name tools.aistarfish.com;

╔════════════════════════════════════════════════╗
║            ✅ 检查完成                         ║
╚════════════════════════════════════════════════╝
```

#### 7.5 访问测试

```bash
# 从本地测试访问
curl -I http://192.168.51.67:8080/your-tool/health
curl -I http://tools.aistarfish.com/your-tool/health

# 浏览器访问
open http://192.168.51.67:8080/your-tool/ui
open http://tools.aistarfish.com/your-tool/ui
```

---

### 🔄 代码更新流程

当需要更新已部署的工具时：

```bash
# 1. 拉取最新代码
git pull origin master

# 2. 修改代码
# ... 进行开发 ...

# 3. 本地测试
./start-all.sh
# 测试通过

# 4. 提交代码
git add .
git commit -m "🐛 修复: XXX问题"
git push origin master

# 5. 重新打包
./package.sh

# 6. 重新部署（会自动备份数据）
./remote-docker-deploy.sh
```

---

### ⚡ 快速命令参考

```bash
# === 开发阶段 ===
git clone <repo-url>                    # 克隆代码
git checkout -b feature/xxx             # 创建分支
./start-all.sh                          # 启动测试
./stop-all.sh                           # 停止测试
./docker-start.sh                       # Docker测试
git add . && git commit -m "xxx"        # 提交代码
git push origin <branch>                # 推送代码

# === 部署阶段 ===
./package.sh                            # 打包
./remote-docker-deploy.sh               # 部署Docker
./setup-nginx.sh                        # 配置Nginx
./check-services.sh                     # 检查状态
```

---

### 📝 开发流程总结

| 阶段 | 关键命令 | 耗时 | 检查点 |
|------|---------|------|--------|
| 1. 环境准备 | `python --version`, `git --version` | 10分钟 | 软件已安装 |
| 2. 拉取代码 | `git clone` | 2分钟 | 代码已下载 |
| 3. 本地开发 | 编写代码、创建文件 | 数小时 | 功能已实现 |
| 4. 本地测试 | `./start-all.sh` | 10分钟 | 测试通过 |
| 5. 提交代码 | `git add`, `git commit`, `git push` | 5分钟 | 代码已推送 |
| 6. 打包发布 | `./package.sh` | 2分钟 | 打包成功 |
| 7. 生产部署 | `./remote-docker-deploy.sh` | 5-10分钟 | 部署成功 |

**总计**：首次完整流程约 **2-4小时**（不含开发时间）

---

## ⚙️ 配置说明

### tools.json 配置文件

所有工具通过 `tools.json` 进行统一配置和管理：

```json
{
  "brand": {
    "title": "海心AI工具集",
    "link": "/ai-model-compare/ui"
  },
  "tools": [
    {
      "id": "your-tool-id",              // 工具唯一标识
      "name": "工具名称",                 // 显示名称
      "icon": "🔧",                       // emoji 图标
      "description": "工具描述",          // 简短描述
      "enabled": true,                    // 是否启用
      "owner": {                          // 技术支持负责人（可选）
        "name": "技术团队",
        "email": "support@example.com",
        "contact": "请联系技术支持团队"
      },
      "service": {
        "type": "fastapi",                // 服务类型：fastapi/flask
        "port": 8080,                     // 服务端口
        "path_prefix": "/your-tool",     // URL 前缀
        "health_check": "/your-tool/health" // 健康检查路径
      },
      "pages": [                          // 子页面列表
        {
          "key": "main",
          "title": "主页面",
          "path": "/your-tool/ui",
          "icon": "🏠"
        }
      ]
    }
  ]
}
```

### 配置项详解

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 工具唯一标识，建议使用小写字母+连字符 |
| `name` | string | 是 | 工具显示名称 |
| `icon` | string | 是 | emoji 图标（推荐使用单个 emoji） |
| `description` | string | 是 | 工具简短描述（1-2句话） |
| `enabled` | boolean | 是 | 是否启用该工具 |
| `owner.name` | string | 否 | 技术支持负责人/团队名称 |
| `owner.email` | string | 否 | 技术支持邮箱 |
| `owner.contact` | string | 否 | 联系方式说明 |
| `service.type` | string | 是 | 服务框架类型（fastapi/flask/express） |
| `service.port` | number | 是 | 服务监听端口 |
| `service.path_prefix` | string | 是 | URL 路径前缀，必须以 `/` 开头 |
| `service.health_check` | string | 是 | 健康检查接口路径 |
| `pages` | array | 是 | 工具的子页面列表 |
| `pages[].key` | string | 是 | 页面唯一标识 |
| `pages[].title` | string | 是 | 页面显示名称 |
| `pages[].path` | string | 是 | 页面访问路径 |
| `pages[].icon` | string | 是 | 页面图标 |

---

## 📐 开发规范

### 1. 目录结构

每个工具应遵循以下目录结构：

```
your-tool/
├── app/                    # 应用代码（FastAPI）
│   ├── __init__.py
│   └── main.py
├── templates/              # HTML 模板
│   └── index.html
├── static/                 # 静态资源（可选）
│   ├── style.css
│   └── app.js
├── Dockerfile             # Docker 配置
├── requirements.txt       # Python 依赖
├── start.sh              # 启动脚本
└── README.md             # 工具说明文档
```

### 2. 导航栏集成

所有页面的 HTML 模板必须包含导航栏容器和加载脚本：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>工具名称</title>
    <!-- 引入导航栏样式 -->
    <link rel="stylesheet" href="/static/nav.css?v=2">
    <!-- 引入 favicon -->
    <link rel="icon" type="image/x-icon" 
          href="https://static.aistarfish.com/front-release/file/F2021082014202908600003617.bitbug_favicon(1).ico">
</head>
<body style="padding: 0;">
    <!-- 导航栏容器 -->
    <div id="haixin-nav"></div>
    
    <!-- 你的页面内容 -->
    <div class="container">
        <!-- ... -->
    </div>
    
    <!-- 导航栏脚本（必须放在页面底部） -->
    <script defer src="/static/nav.js?v=2"></script>
</body>
</html>
```

### 3. 健康检查接口

每个工具必须提供健康检查接口：

**FastAPI 示例：**
```python
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/your-tool")

@router.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"
```

**Flask 示例：**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/your-tool/health')
def health():
    return jsonify({"service": "your-tool", "status": "ok"})
```

### 4. 路由规范

- 所有路由必须使用统一的路径前缀（与 `tools.json` 中的 `path_prefix` 保持一致）
- 主页面路由建议使用 `/your-tool/ui`
- API 路由建议使用 `/your-tool/api/*`
- 静态资源路由统一使用 `/static/*`

---

## 🔧 集成步骤

### 步骤 1：创建工具目录

```bash
cd /path/to/haixin-tools
mkdir your-tool
cd your-tool
```

### 步骤 2：开发工具

参考现有工具（`ai-model-compare` 或 `excelParseTools`）的结构开发您的工具。

**最小化 FastAPI 示例：**

```python
# your-tool/app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR.parent.parent / "ai-model-compare" / "static")), name="static")

@app.get("/your-tool/health")
async def health():
    return "ok"

@app.get("/your-tool/ui")
async def ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

### 步骤 3：创建启动脚本

```bash
# your-tool/start.sh
#!/bin/bash

cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    python3.11 -m venv .venv
fi

source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt -q

# 启动服务
PORT=8080  # 替换为你的端口
uvicorn app.main:app --host 0.0.0.0 --port $PORT &

echo $! > .tool.pid
echo "✓ 工具已启动 (PID: $(cat .tool.pid))"
```

### 步骤 4：更新 tools.json

在 `tools.json` 的 `tools` 数组中添加您的工具配置：

```json
{
  "id": "your-tool",
  "name": "你的工具名称",
  "icon": "🔧",
  "description": "工具描述",
  "enabled": true,
  "service": {
    "type": "fastapi",
    "port": 8080,
    "path_prefix": "/your-tool",
    "health_check": "/your-tool/health"
  },
  "pages": [
    {
      "key": "main",
      "title": "主页面",
      "path": "/your-tool/ui",
      "icon": "🏠"
    }
  ]
}
```

### 步骤 5：更新统一启动脚本

编辑 `start-all.sh`，添加您的工具启动命令：

```bash
# 启动你的工具
start_tool "你的工具名称" "your-tool" "start.sh"
```

### 步骤 6：创建 Dockerfile（可选）

如果需要 Docker 部署，创建 `Dockerfile`：

```dockerfile
FROM registry.cn-shanghai.aliyuncs.com/hxzh_dev/hxzh-python:3.11

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 步骤 7：测试工具

```bash
# 启动单个工具测试
cd your-tool
./start.sh

# 或启动所有工具
cd ..
./start-all.sh

# 访问测试
curl http://localhost:8080/your-tool/health
```

---

## 📦 部署流程

### 本地开发部署

#### 方式 1：直接运行（推荐用于开发调试）

```bash
# 启动所有工具
./start-all.sh

# 停止所有工具
./stop-all.sh

# 单独启动某个工具
cd your-tool
./start.sh
```

**优点**：快速启动，方便调试  
**适用场景**：本地开发、快速测试

#### 方式 2：Docker 本地运行（推荐用于测试）

```bash
# 启动 Docker 容器
./docker-start.sh

# 停止 Docker 容器
./docker-stop.sh
```

**优点**：环境隔离，接近生产环境  
**适用场景**：集成测试、环境验证

---

### 生产环境部署

#### 📋 部署脚本说明

| 脚本 | 用途 | 说明 |
|------|------|------|
| `package.sh` | 打包项目代码 | 排除虚拟环境、日志等，生成 tar.gz 包 |
| `remote-docker-deploy.sh` | 部署到远程服务器 | 自动上传、构建、启动 Docker 容器 |
| `setup-nginx.sh` | 配置 Nginx 和 Hosts | 配置反向代理和域名解析 |
| `check-services.sh` | 检查服务状态 | 诊断工具，查看所有服务状态 |

#### 🚀 完整部署流程

**首次部署**：

```bash
# 步骤 1：打包项目代码
./package.sh
# 生成: haixin-tools-YYYYMMDD-HHMMSS.tar.gz

# 步骤 2：部署 Docker 容器到远程服务器
./remote-docker-deploy.sh
# 提示：请输入远程服务器密码: ********
# 
# 自动完成：
# - 上传打包文件
# - 备份旧数据
# - 解压新代码
# - 构建 Docker 镜像
# - 启动容器

# 步骤 3：配置 Nginx 反向代理（可选，用于域名访问）
./setup-nginx.sh
# 提示：请输入远程服务器密码: ********
#
# 自动完成：
# - 配置 hosts 文件
# - 安装 Nginx
# - 配置反向代理
# - 启动 Nginx

# 步骤 4：验证部署
./check-services.sh
# 检查所有服务状态
```

**更新代码**：

```bash
# 1. 打包最新代码
./package.sh

# 2. 重新部署（会自动备份数据）
./remote-docker-deploy.sh
```

#### 🔒 安全特性

**密码安全**：
- ✅ 脚本不包含硬编码密码
- ✅ 运行时提示输入密码（只需输入一次）
- ✅ 使用 `-s` 参数隐藏输入
- ✅ 密码仅在内存中存储
- ✅ 脚本结束自动清除

**数据安全**：
- ✅ 部署前自动备份数据库
- ✅ 部署前自动备份配置文件
- ✅ 支持数据恢复

**访问方式**：

```bash
# 方式 1：直接访问 IP（不需要配置 hosts）
http://192.168.51.67:8000/ai-model-compare/ui
http://192.168.51.67:5001/excel-tools/

# 方式 2：通过 Nginx 访问（需要配置 hosts）
http://tools.aistarfish.com/ai-model-compare/ui
http://tools.aistarfish.com/excel-tools/

# 配置本地 hosts（macOS/Linux）
sudo nano /etc/hosts
# 添加: 192.168.51.67 tools.aistarfish.com
```

---

## 💡 最佳实践

### 1. 端口分配

建议的端口分配范围：
- `8000-8099`: AI/ML 相关工具
- `5000-5099`: 数据处理工具
- `9000-9099`: 其他工具

已使用的端口：
- `8000`: AI 模型对比
- `5001`: Excel 解析工具

### 2. 错误处理

所有 API 接口应提供统一的错误响应格式：

```json
{
  "error": "错误信息",
  "code": "ERROR_CODE",
  "details": {}
}
```

### 3. 日志管理

建议使用统一的日志格式和存储位置：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### 4. 配置管理

使用环境变量或 `.env` 文件管理配置：

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Your Tool"
    api_key: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 5. 静态资源

- 工具特有的静态资源放在工具目录下的 `static/` 文件夹
- 共享的静态资源（如导航栏样式）放在 `ai-model-compare/static/`
- 所有工具通过 `/static/nav.css` 和 `/static/nav.js` 引用导航栏资源

### 6. 数据库

如果工具需要数据库：
- 推荐使用 SQLite（轻量级工具）
- 数据库文件放在 `data/` 目录
- 在 `.gitignore` 和打包脚本中排除数据库文件

---

## 🔍 故障排查

### 导航栏不显示

**问题**：页面加载后导航栏未显示

**解决方案**：
1. 检查是否引入了 `nav.css` 和 `nav.js`
2. 确认 `<div id="haixin-nav"></div>` 容器存在
3. 检查 `tools.json` 或 `config/menus.json` 是否正确配置
4. 打开浏览器控制台查看是否有 JavaScript 错误

### 工具未在导航栏显示

**问题**：工具已配置但未出现在导航栏

**解决方案**：
1. 确认 `tools.json` 中 `enabled` 设置为 `true`
2. 检查 JSON 格式是否正确（使用 `python -m json.tool tools.json`）
3. 重启服务使配置生效
4. 查看 `/ai-model-compare/menus` API 响应是否包含你的工具

### 端口冲突

**问题**：工具启动失败，提示端口已被占用

**解决方案**：
```bash
# 查找占用端口的进程
lsof -i :8080

# 停止进程
kill -9 <PID>

# 或修改工具使用的端口
```

### 远程部署失败

**问题 1**：SSH 连接失败

**解决方案**：
```bash
# 检查网络连通性
ping 192.168.51.67

# 检查 SSH 连接
ssh admin@192.168.51.67

# 如果需要，配置 SSH 密钥
ssh-copy-id admin@192.168.51.67
```

**问题 2**：Docker 容器无法启动

**解决方案**：
```bash
# 1. 使用诊断脚本检查
./check-services.sh

# 2. 登录服务器查看日志
ssh admin@192.168.51.67
sudo docker logs ai-model-compare
sudo docker logs excel-parse-tools

# 3. 检查端口是否被占用
sudo netstat -tunlp | grep -E ":(8000|5001)"

# 4. 重启容器
sudo docker restart ai-model-compare excel-parse-tools
```

**问题 3**：503 Service Unavailable

**原因**：Nginx 正常但后端服务未运行

**解决方案**：
```bash
# 检查 Docker 容器状态
./check-services.sh

# 如果容器未运行，重新部署
./remote-docker-deploy.sh

# 查看 Nginx 错误日志
ssh admin@192.168.51.67 'sudo tail -100 /var/log/nginx/aistarfish-error.log'
```

### 权限问题

**问题**：部署时提示权限不足

**解决方案**：
```bash
# 确保本地脚本有执行权限
chmod +x *.sh

# 在远程服务器上配置 sudo 免密（可选）
# 登录远程服务器
ssh admin@192.168.51.67

# 编辑 sudoers 文件
sudo visudo

# 添加以下行（谨慎使用）
# admin ALL=(ALL) NOPASSWD: ALL
```

### 域名无法访问

**问题**：配置了 hosts 但域名无法访问

**解决方案**：
```bash
# 1. 检查本地 hosts 配置
cat /etc/hosts | grep aistarfish

# 2. 清除浏览器 DNS 缓存（Chrome）
# 访问: chrome://net-internals/#dns
# 点击: Clear host cache

# 3. 测试连通性
curl -I http://tools.aistarfish.com/health

# 4. 检查代理设置
# 确保没有启用影响内网访问的代理
```

---

## 📞 技术支持

如有问题或需要帮助：

- 📧 邮箱：jianwei.w@aistarfish.com
- 📚 项目文档：`README.md`
- 🐛 问题反馈：提交 Issue

---

## 📝 更新日志

### 2025-10-16
- ✅ **安全性改进**：更新部署流程说明，强调密码安全
- ✅ **部署脚本优化**：新增 `check-services.sh` 诊断工具
- ✅ **文档完善**：
  - 新增生产环境部署详细说明
  - 新增安全特性章节
  - 扩展故障排查内容（远程部署、权限、域名访问）
  - 更新访问方式说明（IP 直接访问 vs 域名访问）

### 2025-10-15
- 📝 初始版本发布
- 📝 添加基础接入指南
- 📝 完善配置说明和开发规范

---

## 🎯 快速参考

### 常用命令

```bash
# 本地开发
./start-all.sh              # 启动所有工具
./stop-all.sh               # 停止所有工具

# Docker 测试
./docker-start.sh           # Docker 启动
./docker-stop.sh            # Docker 停止

# 生产部署
./package.sh                # 打包代码
./remote-docker-deploy.sh   # 部署到远程
./setup-nginx.sh            # 配置 Nginx
./check-services.sh         # 检查服务状态
```

### 常用访问地址

```
本地开发：
- http://localhost:8000/ai-model-compare/ui
- http://localhost:5001/excel-tools/

生产环境（IP直接访问）：
- http://192.168.51.67:8000/ai-model-compare/ui
- http://192.168.51.67:5001/excel-tools/

生产环境（Nginx域名访问）：
- http://tools.aistarfish.com/ai-model-compare/ui
- http://tools.aistarfish.com/excel-tools/
```

### 重要提醒

⚠️ **部署前检查清单**：
- [ ] 代码已提交到 Git
- [ ] 本地测试通过
- [ ] 更新了 `tools.json` 配置
- [ ] 检查端口没有冲突
- [ ] 确认服务器有足够空间
- [ ] 准备好服务器密码

🔐 **安全注意事项**：
- 不要在代码中硬编码密码
- 敏感配置使用环境变量
- 定期备份数据库
- 限制远程访问IP（如需要）

---

**祝开发顺利！🎉**

> 💡 提示：遇到问题？先运行 `./check-services.sh` 诊断，或查看[故障排查](#故障排查)章节。

