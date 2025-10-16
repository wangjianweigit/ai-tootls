#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel解析工具日志管理器
提供可配置的日志记录功能，支持大模型交互日志、批次处理日志等
"""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from config import Config

class LogManager:
    """日志管理器类"""
    
    def __init__(self, task_id: str = None):
        """
        初始化日志管理器
        
        Args:
            task_id: 任务ID，用于区分不同任务的日志
        """
        self.task_id = task_id
        self.config = Config()
        self._setup_loggers()
        
        # 日志缓存，用于实时查看
        self.log_cache: List[Dict[str, Any]] = []
        self.max_cache_size = 1000
        
    def _setup_loggers(self):
        """设置日志记录器"""
        # 确保日志目录存在
        self.config.init_directories()
        
        # 主日志记录器
        self.main_logger = logging.getLogger(f"excel_parser{'_' + self.task_id if self.task_id else ''}")
        self.main_logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # 清除已有的处理器
        self.main_logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.main_logger.addHandler(console_handler)
        
        # 文件处理器
        if self.task_id:
            log_filename = f"task_{self.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        else:
            log_filename = f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(
            self.config.LOG_DIR / log_filename, 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.main_logger.addHandler(file_handler)
        
        # 大模型交互日志记录器
        if self.config.ENABLE_LLM_LOGGING:
            self.llm_logger = logging.getLogger(f"llm_interaction{'_' + self.task_id if self.task_id else ''}")
            self.llm_logger.setLevel(logging.INFO)
            self.llm_logger.handlers.clear()
            
            llm_log_filename = f"llm_{self.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log" if self.task_id else f"llm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            llm_file_handler = logging.FileHandler(
                self.config.LOG_DIR / llm_log_filename,
                encoding='utf-8'
            )
            llm_file_handler.setLevel(logging.INFO)
            llm_file_handler.setFormatter(file_formatter)
            self.llm_logger.addHandler(llm_file_handler)
        else:
            self.llm_logger = None
            
        # 批次处理日志记录器
        if self.config.ENABLE_BATCH_LOGGING:
            self.batch_logger = logging.getLogger(f"batch_processing{'_' + self.task_id if self.task_id else ''}")
            self.batch_logger.setLevel(logging.INFO)
            self.batch_logger.handlers.clear()
            
            batch_log_filename = f"batch_{self.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log" if self.task_id else f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            batch_file_handler = logging.FileHandler(
                self.config.LOG_DIR / batch_log_filename,
                encoding='utf-8'
            )
            batch_file_handler.setLevel(logging.INFO)
            batch_file_handler.setFormatter(file_formatter)
            self.batch_logger.addHandler(batch_file_handler)
        else:
            self.batch_logger = None
    
    def _add_to_cache(self, level: str, message: str, extra_data: Dict[str, Any] = None):
        """添加日志到缓存"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'extra_data': extra_data or {}
        }
        
        self.log_cache.append(log_entry)
        
        # 限制缓存大小
        if len(self.log_cache) > self.max_cache_size:
            self.log_cache = self.log_cache[-self.max_cache_size:]
    
    def info(self, message: str, extra_data: Dict[str, Any] = None):
        """记录信息日志"""
        self.main_logger.info(message)
        self._add_to_cache('INFO', message, extra_data)
    
    def warning(self, message: str, extra_data: Dict[str, Any] = None):
        """记录警告日志"""
        self.main_logger.warning(message)
        self._add_to_cache('WARNING', message, extra_data)
    
    def error(self, message: str, extra_data: Dict[str, Any] = None):
        """记录错误日志"""
        self.main_logger.error(message)
        self._add_to_cache('ERROR', message, extra_data)
    
    def debug(self, message: str, extra_data: Dict[str, Any] = None):
        """记录调试日志"""
        self.main_logger.debug(message)
        self._add_to_cache('DEBUG', message, extra_data)
    
    def log_llm_request(self, prompt: str, rule_id: str, batch_info: Dict[str, Any] = None):
        """记录大模型API请求"""
        if not self.config.ENABLE_LLM_LOGGING or not self.llm_logger:
            return
            
        log_data = {
            'rule_id': rule_id,
            'prompt_length': len(prompt),
            'batch_info': batch_info or {},
            'timestamp': datetime.now().isoformat()
        }
        
        if self.config.LOG_API_REQUESTS:
            log_data['prompt'] = prompt
            
        message = f"LLM API请求 - 规则ID: {rule_id}, 提示词长度: {len(prompt)}"
        self.llm_logger.info(message, extra=log_data)
        self._add_to_cache('LLM_REQUEST', message, log_data)
    
    def log_llm_response(self, response: str, rule_id: str, batch_info: Dict[str, Any] = None, 
                        processing_time: float = None, success: bool = True):
        """记录大模型API响应"""
        if not self.config.ENABLE_LLM_LOGGING or not self.llm_logger:
            return
            
        log_data = {
            'rule_id': rule_id,
            'response_length': len(response),
            'processing_time': processing_time,
            'success': success,
            'batch_info': batch_info or {},
            'timestamp': datetime.now().isoformat()
        }
        
        if self.config.LOG_API_RESPONSES:
            log_data['response'] = response
            
        status = "成功" if success else "失败"
        message = f"LLM API响应 - 规则ID: {rule_id}, 状态: {status}, 响应长度: {len(response)}"
        if processing_time:
            message += f", 处理时间: {processing_time:.2f}秒"
            
        self.llm_logger.info(message, extra=log_data)
        self._add_to_cache('LLM_RESPONSE', message, log_data)
    
    def log_batch_start(self, batch_num: int, batch_size: int, total_records: int, 
                       start_index: int, end_index: int):
        """记录批次处理开始"""
        if not self.config.ENABLE_BATCH_LOGGING or not self.batch_logger:
            return
            
        message = f"批次处理开始 - 批次: {batch_num}, 大小: {batch_size}, 范围: {start_index}-{end_index}/{total_records}"
        self.batch_logger.info(message)
        self._add_to_cache('BATCH_START', message, {
            'batch_num': batch_num,
            'batch_size': batch_size,
            'total_records': total_records,
            'start_index': start_index,
            'end_index': end_index
        })
    
    def log_batch_complete(self, batch_num: int, success_count: int, total_count: int, 
                          processing_time: float, errors: List[str] = None):
        """记录批次处理完成"""
        if not self.config.ENABLE_BATCH_LOGGING or not self.batch_logger:
            return
            
        message = f"批次处理完成 - 批次: {batch_num}, 成功: {success_count}/{total_count}, 耗时: {processing_time:.2f}秒"
        if errors:
            message += f", 错误数: {len(errors)}"
            
        self.batch_logger.info(message)
        self._add_to_cache('BATCH_COMPLETE', message, {
            'batch_num': batch_num,
            'success_count': success_count,
            'total_count': total_count,
            'processing_time': processing_time,
            'errors': errors or []
        })
    
    def log_task_progress(self, task_id: str, processed_records: int, total_records: int, 
                         progress_percentage: float, current_status: str):
        """记录任务进度"""
        message = f"任务进度更新 - {task_id}: {processed_records}/{total_records} ({progress_percentage:.1f}%) - 状态: {current_status}"
        self.info(message, {
            'task_id': task_id,
            'processed_records': processed_records,
            'total_records': total_records,
            'progress_percentage': progress_percentage,
            'current_status': current_status
        })
    
    def log_rule_processing(self, rule_id: str, source_column: str, target_columns: List[str], 
                           record_count: int, success: bool, error_message: str = None):
        """记录规则处理结果"""
        if not self.config.ENABLE_DETAILED_LOGGING:
            return
            
        status = "成功" if success else "失败"
        message = f"规则处理 - {rule_id}: {source_column} -> {target_columns}, 记录数: {record_count}, 状态: {status}"
        if not success and error_message:
            message += f", 错误: {error_message}"
            
        self.info(message, {
            'rule_id': rule_id,
            'source_column': source_column,
            'target_columns': target_columns,
            'record_count': record_count,
            'success': success,
            'error_message': error_message
        })
    
    def get_log_cache(self, level: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """获取日志缓存"""
        if level:
            filtered_logs = [log for log in self.log_cache if log['level'] == level]
        else:
            filtered_logs = self.log_cache.copy()
            
        if limit:
            filtered_logs = filtered_logs[-limit:]
            
        return filtered_logs
    
    def clear_log_cache(self):
        """清空日志缓存"""
        self.log_cache.clear()
    
    def export_logs(self, file_path: str = None) -> str:
        """导出日志到文件"""
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self.config.LOG_DIR / f"exported_logs_{timestamp}.json"
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'task_id': self.task_id,
            'log_count': len(self.log_cache),
            'logs': self.log_cache
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def get_log_summary(self) -> Dict[str, Any]:
        """获取日志摘要统计"""
        if not self.log_cache:
            return {}
        
        level_counts = {}
        for log in self.log_cache:
            level = log['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            'total_logs': len(self.log_cache),
            'level_counts': level_counts,
            'first_log_time': self.log_cache[0]['timestamp'] if self.log_cache else None,
            'last_log_time': self.log_cache[-1]['timestamp'] if self.log_cache else None
        } 