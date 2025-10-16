#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel半结构化数据解析工具启动脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config, Config
from web_interface import app

def main():
    """主函数"""
    print("=" * 60)
    print("Excel半结构化数据解析工具")
    print("=" * 60)
    
    # 获取配置
    config = get_config()
    
    # 初始化目录
    Config.init_directories()
    
    print(f"配置环境: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"数据目录: {Config.DATA_DIR}")
    print(f"日志目录: {Config.LOG_DIR}")
    print(f"Web服务地址: http://{Config.HOST}:{Config.PORT}")
    print("=" * 60)
    
    try:
        # 启动Flask应用
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 