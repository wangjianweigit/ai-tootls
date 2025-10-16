# 📑 Excel数据解析最佳实践 - 资源索引

> 快速导航，找到你需要的资源

## 🎯 我想...

### 快速了解工具
→ 阅读 [README.md](README.md) - 5分钟了解工具能做什么

### 马上开始使用
→ 跟随 [QUICK_START.md](QUICK_START.md) - 5分钟体验完整流程

### 深入学习技巧
→ 学习 [BEST_PRACTICE.md](BEST_PRACTICE.md) - 30分钟掌握最佳实践

### 查看资源清单
→ 浏览 [SUMMARY.md](SUMMARY.md) - 查看完整资源包

### 使用示例数据
→ 打开 `excel_parser_data/imports/best_practice_sample_50.xlsx` - 50条医疗病例数据

### 复用规则配置
→ 参考 `rule_templates/medical_record_rules.json` - 完整规则模板

### 验证处理结果
→ 运行 `python tools/validate_results.py <文件路径>` - 质量验证工具

---

## 📂 文件结构

```
excelParseTools/
│
├── 📖 文档（按阅读顺序）
│   ├── INDEX.md                 ⭐ 本文档 - 快速导航
│   ├── README.md               📘 工具总览（必读）
│   ├── QUICK_START.md          🚀 5分钟快速开始（推荐）
│   ├── BEST_PRACTICE.md        📚 详细教程（进阶）
│   └── SUMMARY.md              📋 资源汇总
│
├── 📊 示例数据
│   └── excel_parser_data/imports/
│       └── best_practice_sample_50.xlsx  ⭐ 50条医疗病例
│
├── 🎯 配置模板
│   └── rule_templates/
│       └── medical_record_rules.json     ⭐ 规则配置模板
│
└── 🛠️ 实用工具
    └── tools/
        └── validate_results.py           ⭐ 结果验证脚本
```

---

## 🎓 学习路径

### 👶 新手路径（总计约30分钟）
1. 📘 README.md（5分钟）- 了解工具
2. 🚀 QUICK_START.md（10分钟）- 实际操作
3. ✅ 验证结果（5分钟）- 使用验证工具
4. 📋 SUMMARY.md（5分钟）- 浏览资源
5. 📚 BEST_PRACTICE.md（随时查阅）- 深入技巧

### 🎯 实战路径（按需）
1. 📊 准备数据 - 参考示例格式
2. 🎯 设计规则 - 基于模板调整
3. 🧪 小批测试 - 10-20条验证
4. ✅ 质量检查 - 使用验证工具
5. 🚀 批量处理 - 处理全部数据

### 💡 高级路径（深度优化）
1. 📚 BEST_PRACTICE.md - 学习高级技巧
2. 🔍 研究源码 - 理解实现原理
3. 🎨 定制规则 - 优化提示词
4. ⚡ 性能调优 - 参数优化
5. 🔄 流程集成 - 业务系统对接

---

## 🔗 快速链接

### 在线访问
- 🏠 工具首页：http://localhost:5001/excel-tools/
- 📋 任务管理：http://localhost:5001/excel-tools/tasks

### 本地文件
- 📊 示例数据：[best_practice_sample_50.xlsx](excel_parser_data/imports/best_practice_sample_50.xlsx)
- 🎯 规则模板：[medical_record_rules.json](rule_templates/medical_record_rules.json)
- 🛠️ 验证工具：[validate_results.py](tools/validate_results.py)

---

## 💬 常见场景

### 场景1：第一次使用
```
1. 启动服务：./start.sh
2. 打开浏览器访问首页
3. 按照 QUICK_START.md 操作
4. 体验完整流程
```

### 场景2：处理自己的数据
```
1. 参考示例数据准备格式
2. 基于规则模板调整配置
3. 小批量测试（10条）
4. 验证结果并优化
5. 批量处理全部数据
```

### 场景3：优化提取质量
```
1. 使用验证工具分析结果
2. 识别准确率低的字段
3. 参考 BEST_PRACTICE.md 优化提示词
4. 重新测试验证
5. 迭代优化
```

### 场景4：了解工具原理
```
1. 阅读 README.md 了解架构
2. 查看 BEST_PRACTICE.md 技术细节
3. 研究源码实现
4. 自定义扩展功能
```

---

## 📊 资源统计

| 类型 | 数量 | 说明 |
|-----|------|------|
| 📖 文档 | 5个 | 完整的学习和参考资料 |
| 📊 示例数据 | 50条 | 医疗病例真实场景模拟 |
| 🎯 规则模板 | 5个规则 | 即用型配置模板 |
| 🛠️ 实用工具 | 1个 | 结果验证脚本 |

**总学习时间：** 5分钟（快速）～ 1小时（深入）  
**数据复杂度：** 中高级  
**适用场景：** 医疗、客服、问卷等半结构化文本提取

---

## 🎯 下一步

### 选择你的起点：

- 🆕 **完全新手**？→ 从 [QUICK_START.md](QUICK_START.md) 开始
- 📚 **想深入学习**？→ 阅读 [BEST_PRACTICE.md](BEST_PRACTICE.md)
- 🔍 **查找资源**？→ 浏览 [SUMMARY.md](SUMMARY.md)
- 💡 **了解功能**？→ 参考 [README.md](README.md)

---

**现在就开始吧！** 🚀

选择一个入口，开启你的数据解析之旅！

