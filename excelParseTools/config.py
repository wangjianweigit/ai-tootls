#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel半结构化数据解析工具配置文件
"""

import os
from pathlib import Path

class Config:
    """应用配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}
    
    # API配置
    MOONSHOT_API_KEY = os.environ.get('MOONSHOT_API_KEY') or "gJrVzbTcTtitntvY5sdNE2tMHdM2O8AH8j9l5q48TV3gJNkh"
    MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1/chat/completions"
    MOONSHOT_MODEL = "kimi-k2-0711-preview"
    MOONSHOT_TEMPERATURE = 0.6
    MOONSHOT_MAX_TOKENS = 127000
    
    # 处理配置
    DEFAULT_BATCH_SIZE = 10
    MAX_RETRIES = 5
    RETRY_DELAY = 0.2  # 秒
    
    # 目录配置
    BASE_DIR = Path(os.getcwd())
    DATA_DIR = BASE_DIR / "excel_parser_data"
    IMPORT_DIR = DATA_DIR / "imports"
    EXPORT_DIR = DATA_DIR / "exports"
    TEMP_DIR = DATA_DIR / "temp"
    LOG_DIR = BASE_DIR / "logs"
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = LOG_DIR / "app.log"
    ERROR_LOG_FILE = LOG_DIR / "error.log"
    
    # 新增：日志控制配置
    ENABLE_LLM_LOGGING = os.environ.get('ENABLE_LLM_LOGGING', 'True').lower() == 'true'  # 是否启用大模型交互日志
    ENABLE_BATCH_LOGGING = os.environ.get('ENABLE_BATCH_LOGGING', 'True').lower() == 'true'  # 是否启用批次处理日志
    ENABLE_DETAILED_LOGGING = os.environ.get('ENABLE_DETAILED_LOGGING', 'False').lower() == 'true'  # 是否启用详细日志
    LOG_API_REQUESTS = os.environ.get('LOG_API_REQUESTS', 'True').lower() == 'true'  # 是否记录API请求详情
    LOG_API_RESPONSES = os.environ.get('LOG_API_RESPONSES', 'False').lower() == 'true'  # 是否记录API响应详情
    
    # Web服务配置
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    
    @classmethod
    def init_directories(cls):
        """初始化必要的目录"""
        directories = [
            cls.DATA_DIR,
            cls.IMPORT_DIR,
            cls.EXPORT_DIR,
            cls.TEMP_DIR,
            cls.LOG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    @classmethod
    def get_api_headers(cls):
        """获取API请求头"""
        return {
            "Authorization": f"Bearer sk-{cls.MOONSHOT_API_KEY}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def get_api_payload_template(cls):
        """获取API请求模板"""
        return {
            "model": cls.MOONSHOT_MODEL,
            "stream": False,
            "temperature": cls.MOONSHOT_TEMPERATURE,
            "max_tokens": cls.MOONSHOT_MAX_TOKENS
        }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """获取配置对象"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default']) 