# 海心AI工具集

一个可扩展的 AI 工具集成平台，支持动态添加和管理多个工具，统一的导航栏和用户体验。

## 🎯 特性

- **统一导航栏** - 所有工具共享一个智能导航系统
- **动态工具注册** - 通过配置文件轻松添加新工具
- **独立服务运行** - 每个工具独立端口，互不干扰
- **优雅的 UI** - 现代化、响应式设计
- **快速部署** - 一键启动/停止所有工具
- **安全部署** - 密码不保存，一次输入即可完成部署

## 📜 部署脚本说明

### 本地开发脚本

| 脚本 | 用途 | 使用场景 |
|------|------|----------|
| `start-all.sh` | 启动所有工具（Python直接运行） | 本地开发调试 |
| `stop-all.sh` | 停止所有工具 | 停止本地服务 |
| `docker-start.sh` | Docker方式启动（使用docker-compose） | 本地Docker测试 |
| `docker-stop.sh` | Docker方式停止 | 停止本地Docker |

### 远程部署脚本

| 脚本 | 用途 | 使用场景 | 推荐度 |
|------|------|----------|--------|
| `package-auto.sh` | 智能自动打包（基于tools.json） | 新项目、团队协作 | ⭐⭐⭐⭐⭐ |
| `package.sh` | 半自动打包 | 现有项目、稳定使用 | ⭐⭐⭐⭐ |
| `remote-docker-deploy.sh` | 部署到远程服务器 | 生产环境部署 | ⭐⭐⭐⭐⭐ |
| `setup-nginx.sh` | 配置Nginx反向代理和hosts | Web服务器配置 | ⭐⭐⭐⭐ |
| `check-services.sh` | 检查远程服务状态 | 诊断和验证 | ⭐⭐⭐⭐ |
| `test-auto-package.sh` | 预览打包配置（不实际打包） | 测试验证 | ⭐⭐⭐ |

## 📦 已集成工具

### 1. AI模型对比 (8000端口)
多模态AI模型对比工具，支持同时对比多个视觉模型的分析结果。

**功能：**
- 🔬 模型对比 - 同时测试多个模型
- ⚙️ 模型管理 - 添加/编辑/删除模型配置
- 📜 对比历史 - 查看历史对比记录

**访问地址：** http://localhost:8000/ai-model-compare/ui

### 2. Excel解析工具 (5001端口)
Excel半结构化数据智能解析工具，通过AI大模型生成结构化数据。

**功能：**
- 📝 数据解析 - 导入Excel并配置解析规则
- 📋 日志管理 - 查看和管理解析日志

**访问地址：** http://localhost:5001/excel-tools/

## 🚀 快速开始

### 前置条件

- Python 3.11+
- pip

> 💡 **远程服务器 Python 版本过低？** 
> 
> 使用一键脚本安装 Python 3.11：
> ```bash
> ./remote-install-python.sh
> ```
> 详见：[Python 安装指南](PYTHON_INSTALL_GUIDE.md)

### 本地开发

#### 一键启动所有工具

```bash
cd /Users/jacking/tools/tools
./start-all.sh
```

#### 一键停止所有工具

```bash
./stop-all.sh
```

#### 单独启动某个工具

```bash
# AI模型对比
cd ai-model-compare
./restart.sh

# Excel解析工具
cd excelParseTools
./start.sh
```

### 远程部署

#### 🚀 完整部署流程（推荐）

首次部署到远程服务器，按以下步骤操作：

```bash
# 1. 打包项目代码（两种方式任选其一）

# 方式一：智能自动打包（推荐）✨
./package-auto.sh
# 基于 tools.json 自动发现工具，无需修改脚本

# 方式二：半自动打包
./package.sh
# 稳定可靠，适合现有项目

# 2. 部署Docker容器到远程服务器
./remote-docker-deploy.sh
# 提示输入密码一次，自动完成所有部署

# 3. 配置Nginx反向代理（可选，用于域名访问）
./setup-nginx.sh
# 提示输入密码一次，自动配置Nginx和hosts

# 4. 验证部署
./check-services.sh
# 查看所有服务状态
```

**💡 打包方式对比**：

| 特性 | package-auto.sh | package.sh |
|------|----------------|------------|
| 添加新工具 | 只需修改 tools.json | 需要修改脚本 + JSON |
| 维护成本 | 低（配置化） | 中等（需要懂bash） |
| 推荐场景 | 新项目、团队协作 | 现有项目、特殊需求 |

**前置条件**：
- 已通过VPN连接到远程网络
- 远程服务器已安装Docker
- 已安装 `sshpass`（macOS: `brew install hudochenkov/sshpass/sshpass`）

#### 🔄 更新已部署的服务

如果服务已经部署，只需要更新代码：

```bash
# 1. 打包最新代码（推荐使用智能打包）
./package-auto.sh  # 或 ./package.sh

# 2. 重新部署
./remote-docker-deploy.sh
# 会自动备份数据并更新服务
```

执行后会询问：
1. 是否上传到远程服务器？
2. 是否自动解压并启动？

#### 方式 3：手动部署

```bash
# 1. 打包
./package-auto.sh  # 或 ./package.sh

# 2. 手动上传
scp haixin-tools-*.tar.gz admin@192.168.51.67:/home/admin/

# 3. SSH登录远程服务器
ssh admin@192.168.51.67

# 4. 解压并启动
cd /home/admin
tar -xzf haixin-tools-*.tar.gz
cd haixin-tools
./start-all.sh
```

**📦 测试打包配置**：

```bash
# 预览打包配置（不实际打包）
./test-auto-package.sh

# 查看将要打包的文件
tar -tzf haixin-tools-*.tar.gz | head -20
```

### 远程服务器配置

当前配置的远程服务器：
- **IP**: 192.168.51.67
- **用户**: admin
- **端口**: SSH默认端口(22)

修改远程服务器配置：
- 编辑 `package.sh` 和 `package-auto.sh` 中的 `REMOTE_*` 变量
- 编辑 `remote-docker-deploy.sh` 中的 `REMOTE_*` 变量
- 编辑 `setup-nginx.sh` 中的 `REMOTE_*` 变量

## 🔧 添加新工具

### 1. 修改 `tools.json` 配置文件

在根目录的 `tools.json` 文件中添加新工具配置：

```json
{
  "tools": [
    {
      "id": "your-tool-id",
      "name": "你的工具名称",
      "icon": "🎨",
      "description": "工具描述",
      "enabled": true,
      "directory": "your-tool-dir",  // 关键：用于自动打包
      "service": {
        "type": "flask|fastapi|express",
        "port": 5002,
        "path_prefix": "/your-tool",
        "health_check": "/your-tool/health"
      },
      "packaging": {  // 可选：打包排除规则
        "exclude": [
          "__pycache__",
          "*.pyc",
          ".venv",
          "*.log",
          "data/"
        ]
      },
      "pages": [
        {
          "key": "main",
          "title": "主页",
          "path": "/your-tool/",
          "icon": "🏠"
        }
      ]
    }
  ]
}
```

### 2. 在工具的HTML模板中添加导航栏

```html
<!DOCTYPE html>
<html>
<head>
    <!-- 引入导航栏样式和脚本 -->
    <link rel="stylesheet" href="http://localhost:8000/static/nav.css?v=2">
    <script defer src="http://localhost:8000/static/nav.js?v=2"></script>
</head>
<body style="padding: 0; margin: 0;">
    <!-- 导航栏容器 -->
    <div id="haixin-nav"></div>
    
    <!-- 你的页面内容 -->
    <div class="container">
        ...
    </div>
</body>
</html>
```

### 3. 创建启动脚本

参考 `excelParseTools/start.sh` 创建你的工具启动脚本。

### 4. 更新 `start-all.sh`

在统一启动脚本中添加你的工具：

```bash
start_tool "你的工具名" "your-tool-dir" "start.sh"
```

## 📂 目录结构

```
tools/
├── tools.json                  # 全局工具配置文件
├── start-all.sh               # 统一启动脚本
├── stop-all.sh                # 统一停止脚本
├── README.md                  # 本文档
│
├── ai-model-compare/          # AI模型对比工具
│   ├── app/                   # 应用代码
│   ├── static/                # 静态资源（含导航栏）
│   ├── templates/             # HTML模板
│   ├── restart.sh             # 重启脚本
│   └── ...
│
└── excelParseTools/           # Excel解析工具
    ├── templates/             # HTML模板
    ├── start.sh               # 启动脚本
    └── ...
```

## 🎨 导航栏工作原理

1. **全局配置** - `tools.json` 定义所有工具和页面
2. **菜单 API** - AI模型对比工具提供 `/ai-model-compare/menus` API
3. **前端组件** - `nav.js` 和 `nav.css` 实现导航栏UI
4. **动态加载** - 页面加载时自动从API获取菜单配置并渲染

## 🔗 工具间导航规则

- **同一工具内** - 在当前标签页跳转
- **不同工具间** - 在新标签页打开

## 🛠️ 管理命令

### 查看所有服务状态

```bash
ps aux | grep -E '(uvicorn|flask|python.*run.py)'
```

### 查看端口占用

```bash
lsof -i :8000  # AI模型对比
lsof -i :5001  # Excel解析工具
```

### 查看日志

```bash
# AI模型对比
tail -f ai-model-compare/app.log

# Excel解析工具
tail -f excelParseTools/excel_parser.log
```

## 🌐 使用 Nginx 统一端口（可选）

如果你想通过单一端口（如80）访问所有工具，可以配置 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name tools.example.com;

    # AI模型对比
    location /ai-model-compare/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Excel解析工具
    location /excel-tools/ {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态资源
    location /static/ {
        proxy_pass http://localhost:8000/static/;
    }
}
```

## 📝 配置文件说明

### `tools.json` 字段说明

- `brand` - 品牌配置（标题和链接）
- `tools` - 工具列表
  - `id` - 工具唯一标识
  - `name` - 工具显示名称
  - `icon` - 工具图标（Emoji）
  - `description` - 工具描述
  - `enabled` - 是否启用（false时不显示在导航栏）
  - `service` - 服务配置
    - `type` - 服务类型
    - `port` - 服务端口
    - `path_prefix` - URL路径前缀
    - `health_check` - 健康检查接口
  - `pages` - 页面列表
    - `key` - 页面唯一标识
    - `title` - 页面标题
    - `path` - 页面路径
    - `icon` - 页面图标

## 🤝 贡献

欢迎添加新工具到海心AI工具集！请遵循以下步骤：

1. 在 `tools.json` 中注册你的工具
2. 在工具的HTML模板中集成导航栏
3. 创建启动脚本
4. 更新本文档
5. 测试所有功能正常

## 📚 文档索引

完整的开发和部署文档：

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| **[README.md](README.md)** | 项目概览和快速开始 | 所有用户 |
| **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** | 完整开发流程指南 | 开发者 |
| **[PACKAGING_GUIDE.md](PACKAGING_GUIDE.md)** | 打包指南（三种方案对比） | 运维、开发者 |
| **[AUTO_PACKAGE_SETUP.md](AUTO_PACKAGE_SETUP.md)** | 自动打包配置说明 | 运维 |
| **[FULL_DEPLOYMENT_GUIDE.md](FULL_DEPLOYMENT_GUIDE.md)** | 完整部署指南 | 运维 |

---

## 🙋 常见问题

### Q: 为什么不同工具在不同端口？
A: 这样可以让每个工具独立运行，互不影响，便于开发和维护。如需统一端口，可使用Nginx反向代理。

### Q: 如何禁用某个工具？
A: 在 `tools.json` 中将该工具的 `enabled` 设置为 `false`。

### Q: 导航栏样式如何自定义？
A: 修改 `ai-model-compare/static/nav.css` 文件。

### Q: 新添加的工具需要重启其他工具吗？
A: 不需要，只需启动新工具即可。导航栏会自动读取最新的 `tools.json` 配置。

### Q: package.sh 和 package-auto.sh 有什么区别？
A: `package-auto.sh` 完全基于 `tools.json` 自动发现工具，添加新工具只需修改 JSON；`package.sh` 需要手动在脚本中配置。推荐新项目使用 `package-auto.sh`。详见 [PACKAGING_GUIDE.md](PACKAGING_GUIDE.md)。

### Q: 如何验证打包配置是否正确？
A: 运行 `./test-auto-package.sh` 可以预览打包配置，不会实际生成包。

## 📮 联系方式

如有问题或建议，请通过以下方式联系：
- 邮件：[jianwei.w@aistarfish.com]
- 企微: 承枫

---

## 🔄 更新日志

### v2.0.0 (2025-10-16)
- ✨ 新增智能自动打包功能 (`package-auto.sh`)
- ✨ 基于 `tools.json` 的统一配置管理
- 📝 完善开发者文档和部署指南
- 🔧 优化打包流程，提升效率 3-5倍
- 🗑️ 清理冗余配置文件

### v1.0.0 (2025-10-10)
- 🎉 初始版本发布
- ✅ AI模型对比工具
- ✅ Excel解析工具
- ✅ 统一导航系统
- ✅ 远程部署脚本

---

**版本**: 2.0.0  
**最后更新**: 2025年10月16日  
**维护者**: 承枫 (AI基础核心团队)
