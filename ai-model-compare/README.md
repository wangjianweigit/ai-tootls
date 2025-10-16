# 🤖 多模态 AI 模型对比系统

一个强大的多模态 AI 模型对比工具，支持同时调用多个视觉语言模型（VLM）并对比结果，帮助你选择最适合的模型。

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能特性

### 核心功能
- 📊 **多模型对比**: 同时调用多个 AI 模型，并排对比结果
- 🖼️ **图像分析**: 支持上传图片进行视觉理解和分析
- 📝 **自定义提示词**: 灵活配置系统提示和用户提示
- 📈 **性能监控**: 实时显示每个模型的响应时间
- 💾 **历史记录**: 自动保存对比历史，支持查看和回溯
- 🔧 **模型管理**: 动态配置和管理多个 AI 模型

### 已支持的模型
- 🌙 **Kimi** (Moonshot AI)
- 🧠 **Qwen** (通义千问)
- 🔥 **Doubao** (豆包)
- 🤖 **OpenAI** (GPT-4 Vision)
- 💬 **Claude** (Anthropic)
- ✨ **Gemini** (Google)
- 🔧 **自定义模型** (支持任意 OpenAI 兼容 API)

### 高级特性
- ⚡ **并发调用**: 异步并发请求，提升响应速度
- 🎨 **现代 UI**: 响应式设计，支持移动端访问
- 🔐 **权限控制**: 管理员模式保护敏感操作
- 📷 **图片预览**: 支持点击放大查看原图
- 🌐 **多路径重试**: 自动尝试多个 API 路径
- 📊 **详细日志**: 完整的请求/响应日志记录

## 🚀 快速开始

### 前置要求
- Python 3.11 或更高版本
- pip 包管理器

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-model-compare
```

2. **创建虚拟环境**
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建 `.env` 文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 密钥：
```env
KIMI_URL=https://api.moonshot.cn
KIMI_KEY=your-kimi-api-key
KIMI_MODEL=moonshot-v1-8k-vision-preview

QWEN_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_KEY=your-qwen-api-key
QWEN_MODEL=qwen-vl-max

DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_API_KEY=your-doubao-api-key
DOUBAO_MODEL=doubao-seed-1-6-250615
```

5. **启动服务**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

6. **访问应用**
- 模型对比页: http://localhost:8000/ui
- 模型管理页: http://localhost:8000/models-ui
- 历史记录页: http://localhost:8000/history-ui

## 📖 使用指南

### 基本使用流程

1. **访问对比页面**
   - 打开 `http://localhost:8000/ui`

2. **配置模型**
   - 在模型管理页 (`/models-ui?manager=true`) 添加和配置模型
   - 或使用默认的环境变量配置

3. **上传图片**
   - 选择要分析的图片文件
   - 输入系统提示词和用户提示词

4. **选择模型**
   - 勾选要对比的模型（可多选）
   - 点击"提交对比"按钮

5. **查看结果**
   - 实时显示各模型的响应结果
   - 对比不同模型的输出差异
   - 查看响应时间和性能

6. **历史记录**
   - 在历史记录页查看之前的对比结果
   - 支持搜索和筛选

### 管理员功能

访问 `http://localhost:8000/models-ui?manager=true` 启用管理员模式：

- ➕ 添加新模型
- 🔄 启用/禁用模型
- 🗑️ 删除模型
- ✏️ 编辑模型配置

## 📂 项目结构

```
ai-model-compare/
├── app/
│   ├── __init__.py          # 数据库初始化
│   ├── main.py              # FastAPI 主应用
│   ├── clients.py           # AI 模型客户端
│   └── config.py            # 配置管理
├── static/
│   ├── app.js               # 对比页面 JS
│   ├── style.css            # 对比页面样式
│   ├── models.js            # 模型管理 JS
│   ├── models.css           # 模型管理样式
│   ├── history.js           # 历史记录 JS
│   └── history.css          # 历史记录样式
├── templates/
│   ├── compare.html         # 对比页面模板
│   ├── models.html          # 模型管理模板
│   └── history.html         # 历史记录模板
├── data/
│   └── history.sqlite3      # SQLite 数据库
├── .env                     # 环境变量配置
├── requirements.txt         # Python 依赖
├── DEPLOYMENT.md            # 部署指南
├── deploy.sh                # 自动部署脚本
└── README.md                # 项目文档
```

## 🔧 配置说明

### 环境变量

所有配置通过 `.env` 文件管理：

| 变量 | 说明 | 必填 |
|------|------|------|
| `KIMI_URL` | Kimi API 地址 | 否 |
| `KIMI_KEY` | Kimi API 密钥 | 否 |
| `KIMI_MODEL` | Kimi 模型名称 | 否 |
| `QWEN_URL` | Qwen API 地址 | 否 |
| `QWEN_KEY` | Qwen API 密钥 | 否 |
| `QWEN_MODEL` | Qwen 模型名称 | 否 |
| `DOUBAO_BASE_URL` | Doubao API 地址 | 否 |
| `DOUBAO_API_KEY` | Doubao API 密钥 | 否 |
| `DOUBAO_MODEL` | Doubao 模型名称 | 否 |
| `DATABASE_URL` | 数据库连接地址 | 否 |
| `SQLITE_PATH` | SQLite 文件路径 | 否 |

### 数据库配置

默认使用 SQLite，数据存储在 `data/history.sqlite3`。

如需使用其他数据库，设置 `DATABASE_URL`：
```env
DATABASE_URL=sqlite:///path/to/database.db
```

## 🌐 部署指南

### 快速部署

使用自动部署脚本：
```bash
chmod +x deploy.sh
./deploy.sh
```

### 生产环境部署

详细的部署步骤请参考 [DEPLOYMENT.md](DEPLOYMENT.md)，包括：

- 系统要求和依赖安装
- 使用 systemd/Supervisor 管理服务
- Nginx 反向代理配置
- HTTPS/SSL 证书配置
- 日志管理和备份策略
- 性能优化建议

### Docker 部署（即将支持）

```bash
docker-compose up -d
```

## 🛠️ 开发指南

### 本地开发

1. 安装开发依赖：
```bash
pip install -r requirements.txt
```

2. 启动开发服务器（支持热重载）：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 添加新模型

1. 在数据库中添加模型配置
2. 或通过管理界面添加
3. 确保 API 兼容 OpenAI 格式

### 代码结构

- `app/main.py` - API 路由和业务逻辑
- `app/clients.py` - 模型调用封装
- `app/config.py` - 配置加载和验证
- `static/` - 前端静态资源
- `templates/` - HTML 模板

## 🐛 故障排查

### 常见问题

**1. 端口被占用**
```bash
lsof -i :8000
kill -9 <PID>
```

**2. API 调用失败**
- 检查 API 密钥是否正确
- 确认网络连接正常
- 查看日志文件：`tail -f app.log`

**3. 数据库错误**
```bash
rm data/history.sqlite3
python3 -c "from app import init_db; init_db()"
```

更多问题请查看 [故障排查指南](TROUBLESHOOTING.md)

## 📊 性能指标

- 并发支持：10+ 并发请求
- 响应时间：< 5s (取决于模型 API)
- 图片支持：最大 10MB
- 历史记录：无限制

## 🔐 安全建议

- ✅ 使用 HTTPS 加密传输
- ✅ 定期轮换 API 密钥
- ✅ 限制管理页面访问
- ✅ 配置防火墙规则
- ✅ 定期备份数据库
- ✅ 监控异常日志

## 📝 API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/ui` | 对比页面 |
| GET | `/models-ui` | 模型管理页 |
| GET | `/history-ui` | 历史记录页 |
| POST | `/compare` | 提交对比请求 |
| GET | `/models` | 获取模型列表 |
| POST | `/models` | 创建新模型 |
| DELETE | `/models/{id}` | 删除模型 |
| PATCH | `/models/{id}/toggle` | 切换模型状态 |
| GET | `/history` | 获取历史列表 |
| GET | `/history/{id}` | 获取历史详情 |

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的 Web 框架
- [HTTPX](https://www.python-httpx.org/) - 异步 HTTP 客户端
- [Uvicorn](https://www.uvicorn.org/) - ASGI 服务器
- 各个 AI 模型提供商

## 📞 联系方式

- 问题反馈：[GitHub Issues](https://github.com/your-repo/issues)
- 功能建议：[GitHub Discussions](https://github.com/your-repo/discussions)

## 🗺️ 路线图

- [ ] Docker 容器化支持
- [ ] 支持更多 AI 模型
- [ ] 批量对比功能
- [ ] 模型性能分析报告
- [ ] 用户认证系统
- [ ] API 速率限制
- [ ] WebSocket 实时推送
- [ ] 导出对比结果

---

⭐ 如果这个项目对你有帮助，欢迎 Star！
