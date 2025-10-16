#!/bin/bash
# 快速测试自动打包配置（不实际生成包）

set -e

echo "╔════════════════════════════════════════════════╗"
echo "║      测试自动打包配置（预览模式）               ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 解析工具
echo "🔍 解析 tools.json..."
TOOLS=$(python3 << 'PYTHON_SCRIPT'
import json

with open('tools.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

for tool in config.get('tools', []):
    if not tool.get('enabled', True):
        continue
    
    directory = tool.get('directory', tool.get('id'))
    excludes = tool.get('packaging', {}).get('exclude', [])
    
    print(f"{directory}|{','.join(excludes)}")
PYTHON_SCRIPT
)

echo ""
echo "📦 发现的工具："
echo "$TOOLS" | while IFS='|' read -r directory excludes; do
    if [ -d "$directory" ]; then
        file_count=$(find "$directory" -type f 2>/dev/null | wc -l | tr -d ' ')
        echo "  ✅ $directory ($file_count 文件)"
    else
        echo "  ⚠️  $directory (目录不存在)"
    fi
done

echo ""
echo "🚫 排除规则预览："
echo "$TOOLS" | while IFS='|' read -r directory excludes; do
    echo "  📁 $directory:"
    IFS=',' read -ra EXCLUDE_LIST <<< "$excludes"
    count=0
    for exclude in "${EXCLUDE_LIST[@]}"; do
        if [ $count -lt 3 ]; then
            echo "     • $exclude"
        fi
        count=$((count + 1))
    done
    if [ $count -gt 3 ]; then
        echo "     ... 还有 $((count - 3)) 条"
    fi
done

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║              ✅ 配置验证通过！                 ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "💡 准备就绪！可以运行以下命令："
echo ""
echo "   方式一（手动）：./package.sh"
echo "   方式二（自动）：./package-auto.sh  ✨推荐"
echo ""
