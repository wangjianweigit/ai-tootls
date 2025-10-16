# 📦 打包指南 - 新应用接入

本文档说明如何将新应用加入打包流程。

---

## 🎯 方案对比

| 方案 | 脚本 | 优点 | 缺点 | 推荐度 |
|------|------|------|------|--------|
| **方案一：智能自动打包** | `package-auto.sh` | ✅ 完全自动发现<br>✅ 零配置<br>✅ 基于 tools.json<br>✅ 最易维护 | ⚠️ 需要 tools.json 配置 | ⭐⭐⭐⭐⭐ |
| **方案二：半自动打包** | `package.sh` | ✅ 自动发现（手动配置）<br>✅ 稳定可靠 | ⚠️ 添加工具需修改脚本 | ⭐⭐⭐⭐ |
| **方案三：手动打包** | 手动修改 | ✅ 灵活性最高<br>✅ 可自定义 | ❌ 每次都要改脚本<br>❌ 容易遗漏 | ⭐⭐⭐ |

---

## 🚀 方案一：智能自动打包（推荐）⭐

### 📋 原理

`package-auto.sh` 自动读取 `tools.json`，智能发现并打包所有工具，无需修改脚本。

### ✨ 特点

- ✅ **完全自动化**：基于 tools.json 自动发现工具
- ✅ **零脚本修改**：添加新工具只需修改 JSON
- ✅ **统一配置**：所有工具配置集中管理
- ✅ **智能排除**：自动应用排除规则
- ✅ **团队协作**：配置即文档，易于理解

### 📝 步骤

#### 1️⃣ 在 tools.json 中添加工具配置

```json
{
  "tools": [
    {
      "id": "your-new-tool",
      "name": "您的新工具",
      "icon": "🔧",
      "description": "工具描述",
      "enabled": true,
      "directory": "your-new-tool",  // 关键：指定目录名
      "service": {
        "type": "fastapi",
        "port": 8002,
        "path_prefix": "/your-new-tool"
      },
      "packaging": {
        "exclude": [
          "__pycache__",
          "*.pyc",
          ".venv",
          "*.log",
          ".pid"
        ]
      }
    }
  ]
}
```

#### 2️⃣ 运行智能打包脚本

```bash
./package-auto.sh
```

脚本会自动：
- ✅ 扫描 tools.json 中所有启用的工具
- ✅ 自动检测到 `your-new-tool` 目录
- ✅ 应用配置的排除规则
- ✅ 打包到 tar.gz
- ✅ 显示打包进度和结果

#### 3️⃣ 验证打包（可选）

```bash
# 预览配置（不实际打包）
./test-auto-package.sh

# 查看打包内容
tar -tzf haixin-tools-*.tar.gz | grep your-new-tool
```

### 🔧 配置说明

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `directory` | ✅ | 工具目录名（相对于项目根目录） | `"ai-model-compare"` |
| `packaging.exclude` | ❌ | 排除的文件/目录（默认值见下文） | `["*.log", "data/"]` |
| `packaging.enabled` | ❌ | 是否打包（默认 true） | `true` |

### 📦 默认排除规则

如果未指定 `packaging.exclude`，使用以下默认规则：

```
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.log
*.pid
.git/
.DS_Store
node_modules/
```

### 🔄 与 package.sh 的区别

| 特性 | package-auto.sh | package.sh |
|------|----------------|------------|
| 工具发现 | 自动从 tools.json 读取 | 手动在脚本中配置 |
| 添加新工具 | 只需修改 JSON | 需要修改脚本 |
| 配置管理 | 集中在 tools.json | 分散在脚本中 |
| 维护成本 | 低 | 中等 |
| 学习曲线 | 简单 | 需要了解 bash |
| 推荐场景 | 新项目、团队协作 | 现有项目、特殊需求 |

---

## 🔧 方案二：半自动打包（package.sh）

### 📋 原理

`package.sh` 通过脚本内的配置进行打包，需要手动添加每个工具。

### 📝 步骤

#### 1️⃣ 在 tools.json 中添加工具配置

```json
{
  "tools": [
    {
      "id": "your-new-tool",
      "name": "您的新工具",
      "icon": "🔧",
      "description": "工具描述",
      "enabled": true,
      "directory": "your-new-tool",  // 关键：指定目录名
      "service": {
        "type": "fastapi",
        "port": 8002,
        "path_prefix": "/your-new-tool"
      },
      "packaging": {
        "exclude": [
          "__pycache__",
          "*.pyc",
          ".venv",
          "*.log",
          ".pid"
        ]
      }
    }
  ]
}
```

#### 2️⃣ 运行打包脚本

```bash
./package.sh
```

**注意：** 如果使用当前版本的 `package.sh`，它已经支持从 `tools.json` 读取配置，效果与 `package-auto.sh` 相同。

---

## 🛠️ 方案三：手动添加（灵活）

### 📝 步骤

#### 1️⃣ 编辑 package.sh

在 `# 复制文件` 部分添加新的 rsync 命令：

```bash
echo "✓ 复制 您的新工具..."
if [ -d "$SCRIPT_DIR/your-new-tool" ]; then
    rsync -av --exclude='__pycache__' \
              --exclude='*.pyc' \
              --exclude='.venv' \
              --exclude='logs/' \
              --exclude='*.log' \
              "$SCRIPT_DIR/your-new-tool/" \
              "$TEMP_DIR/haixin-tools/your-new-tool/"
else
    echo "  ⚠️  your-new-tool 目录不存在，跳过"
    mkdir -p "$TEMP_DIR/haixin-tools/your-new-tool"
fi
```

#### 2️⃣ 添加必要目录创建

在 `# 创建必要目录` 部分添加：

```bash
mkdir -p "$TEMP_DIR/haixin-tools/your-new-tool/data"
mkdir -p "$TEMP_DIR/haixin-tools/your-new-tool/logs"
```

#### 3️⃣ 运行打包

```bash
./package.sh
```

---

## 📂 目录结构要求

新工具应遵循以下结构（自动化打包必需）：

```
your-new-tool/
├── app/                    # 应用代码
│   ├── __init__.py
│   └── main.py
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 配置
├── start.sh               # 启动脚本（可选）
├── config/                # 配置文件（可选）
├── templates/             # 模板文件（可选）
├── static/                # 静态资源（可选）
├── data/                  # 数据目录（运行时生成，不打包）
└── logs/                  # 日志目录（运行时生成，不打包）
```

---

## ✅ 完整示例

### 示例 1：FastAPI 工具

**tools.json 配置：**

```json
{
  "id": "text-analytics",
  "name": "文本分析工具",
  "icon": "📝",
  "directory": "textAnalytics",
  "enabled": true,
  "service": {
    "type": "fastapi",
    "port": 8003,
    "path_prefix": "/text-analytics"
  },
  "packaging": {
    "exclude": [
      "__pycache__",
      ".venv",
      "*.log",
      "data/*.db"
    ]
  }
}
```

**目录结构：**

```
textAnalytics/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── models.py
├── requirements.txt
├── Dockerfile
└── start.sh
```

**运行打包：**

```bash
# 方案一：智能自动打包（推荐）
./package-auto.sh

# 方案二：半自动打包
./package.sh
```

---

### 示例 2：Flask 工具

**tools.json 配置：**

```json
{
  "id": "image-processor",
  "name": "图像处理工具",
  "icon": "🖼️",
  "directory": "imageProcessor",
  "enabled": true,
  "service": {
    "type": "flask",
    "port": 5002,
    "path_prefix": "/image-processor"
  },
  "packaging": {
    "exclude": [
      "__pycache__",
      ".venv",
      "uploads/",
      "temp/"
    ]
  }
}
```

---

## 🔍 验证打包结果

### 1. 查看打包内容

```bash
# 解压到临时目录查看
tar -tzf haixin-tools-*.tar.gz | grep your-new-tool
```

### 2. 验证文件结构

```bash
# 完整解压查看
tar -xzf haixin-tools-*.tar.gz -C /tmp/
tree /tmp/haixin-tools/your-new-tool
```

### 3. 检查排除规则

确认以下文件**未被**打包：
- ✅ `__pycache__/` 目录
- ✅ `.venv/` 虚拟环境
- ✅ `*.log` 日志文件
- ✅ `data/*.db` 数据库文件

---

## 🐛 常见问题

### Q1: 工具没有被打包？

**检查清单：**
- ✅ `tools.json` 中 `enabled: true`
- ✅ `directory` 字段与实际目录名一致
- ✅ 目录存在于项目根目录
- ✅ 运行 `./package-auto.sh` 或 `./package.sh` 时没有报错

**调试方法：**

```bash
# 预览配置（不实际打包）
./test-auto-package.sh

# 检查 tools.json 格式
python3 -m json.tool tools.json
```

### Q2: 打包了不该打包的文件？

**解决方案：**
在 `tools.json` 中添加 `packaging.exclude` 规则：

```json
"packaging": {
  "exclude": [
    "sensitive-data/",
    "*.secret",
    "credentials.json"
  ]
}
```

### Q3: 如何只打包特定工具？

**方案 1（推荐）：** 设置 `enabled: false`

```json
{
  "id": "tool-1",
  "enabled": false,  // 跳过打包
  ...
}
```

**方案 2：** 设置 `packaging.enabled: false`

```json
{
  "id": "tool-1",
  "enabled": true,    // 工具启用
  "packaging": {
    "enabled": false  // 但不打包
  },
  ...
}
```

### Q4: package.sh 和 package-auto.sh 有什么区别？

| 维度 | package.sh | package-auto.sh |
|------|-----------|----------------|
| **工具发现** | 需要手动在脚本中配置 rsync | 自动从 tools.json 读取 |
| **添加工具** | 修改脚本 + 修改 JSON | 只修改 JSON |
| **配置位置** | 脚本中（rsync 参数） | tools.json 中 |
| **维护难度** | 中等（需要懂 bash） | 简单（只需懂 JSON） |
| **灵活性** | 高（可以自定义任何逻辑） | 高（基于配置） |
| **推荐场景** | 特殊需求、现有项目 | 新项目、团队协作 |

**结论：** 
- 新项目推荐使用 `package-auto.sh` ⭐
- 现有项目可以继续使用 `package.sh`
- 两者生成的包格式完全相同

### Q5: 如何从 package.sh 迁移到 package-auto.sh？

**步骤：**

1. 确保 `tools.json` 中所有工具都配置了 `directory` 和 `packaging`
2. 运行 `./test-auto-package.sh` 验证配置
3. 运行 `./package-auto.sh` 测试打包
4. 对比生成的包是否一致：
   ```bash
   ./package.sh
   mv haixin-tools-*.tar.gz old.tar.gz
   
   ./package-auto.sh
   mv haixin-tools-*.tar.gz new.tar.gz
   
   # 对比内容
   tar -tzf old.tar.gz | sort > old.txt
   tar -tzf new.tar.gz | sort > new.txt
   diff old.txt new.txt
   ```
5. 如果一致，可以切换到 `package-auto.sh`

---

## 📚 相关文档

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| **[QUICK_ADD_TOOL.md](QUICK_ADD_TOOL.md)** | 快速添加工具指南 | 快速上手 |
| **[AUTO_PACKAGE_SETUP.md](AUTO_PACKAGE_SETUP.md)** | 自动打包配置说明 | 了解自动打包 |
| **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** | 开发者接入指南 | 开发新工具 |
| **[FULL_DEPLOYMENT_GUIDE.md](FULL_DEPLOYMENT_GUIDE.md)** | 完整部署指南 | 生产部署 |
| **[README.md](README.md)** | 项目总览 | 项目概况 |

---

## 🎉 总结

### 推荐工作流

#### 方式一：智能自动打包（推荐）⭐

1. **开发新工具** → 遵循标准目录结构
2. **添加到 tools.json** → 配置 `directory` 和 `packaging`
3. **运行 package-auto.sh** → 自动打包
4. **验证打包** → 检查 tar.gz 内容
5. **部署** → 使用 `remote-docker-deploy.sh`

```bash
# 一条命令完成打包
./package-auto.sh

# 打包并上传到远程服务器
./package-auto.sh  # 按提示选择 'y' 上传
```

#### 方式二：半自动打包

```bash
# 打包所有启用的工具
./package.sh

# 打包并上传到远程服务器
./package.sh  # 按提示选择 'y' 上传
```

### 📊 三种方案总结

| 使用场景 | 推荐方案 | 命令 |
|---------|---------|------|
| 新项目、团队协作 | 方案一（智能自动） | `./package-auto.sh` ⭐ |
| 现有项目、稳定使用 | 方案二（半自动） | `./package.sh` |
| 特殊需求、精确控制 | 方案三（手动） | 修改脚本 |

### ⚡ 效率对比

| 操作 | 方案一（智能） | 方案二（半自动） | 方案三（手动） |
|------|--------------|----------------|--------------|
| 添加新工具 | 修改 JSON（1分钟） | 修改 JSON + 脚本（5分钟） | 修改脚本（10分钟） |
| 维护成本 | 低 | 中 | 高 |
| 学习曲线 | 简单 | 中等 | 较难 |

---

**更新时间：** 2025-10-16  
**版本：** v2.0（新增智能自动打包）  
**维护者：** AI基础核心团队

