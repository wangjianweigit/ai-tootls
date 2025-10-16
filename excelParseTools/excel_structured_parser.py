#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel半结构化数据解析工具
功能：导入Excel文件，选择列进行解析，通过大模型API生成新的结构化列，支持异步处理和进度跟踪
"""

import os
import sys
import pandas as pd
import requests
import json
import time
import re
import asyncio
import threading
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from pathlib import Path
import uuid
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入日志管理器
from logger_manager import LogManager

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ParsingRule:
    """解析规则数据类"""
    source_column: str  # 源列名
    target_columns: List[str]  # 目标列名列表
    prompt: str  # 解析提示词
    rule_id: str = None  # 规则ID
    
    def __post_init__(self):
        if self.rule_id is None:
            self.rule_id = str(uuid.uuid4())

@dataclass
class ProcessingTask:
    """处理任务数据类"""
    task_id: str
    input_file: str
    output_file: str
    parsing_rules: List[ParsingRule]
    status: TaskStatus
    progress: float  # 0-100
    total_records: int
    processed_records: int
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    threads: int = 1
    checkpoint_every: int = 50  # 每处理多少行保存一次
    partial_output_file: Optional[str] = None
    progress_file: Optional[str] = None
    name: str = ""

class ExcelStructuredParser:
    """Excel半结构化数据解析器"""
    
    def __init__(self, api_key: str = None, base_dir: str = None):
        """
        初始化解析器
        
        Args:
            api_key: 大模型API密钥，如果为None则使用配置文件中的密钥
            base_dir: 基础目录，用于存储导入导出文件
        """
        from config import Config
        
        # 使用配置或传入的API密钥
        self.api_key = api_key or Config.MOONSHOT_API_KEY
        self.base_url = Config.MOONSHOT_BASE_URL
        self.headers = Config.get_api_headers()
        
        # 设置基础目录
        if base_dir is None:
            self.base_dir = Config.DATA_DIR
        else:
            self.base_dir = Path(base_dir)
        
        # 初始化目录
        Config.init_directories()
        
        # 初始化日志管理器
        self.log_manager = LogManager()
        
        # 存储任务信息
        self.tasks: Dict[str, ProcessingTask] = {}
        self._tasks_lock = threading.Lock()
        
        # 存储导入的Excel数据
        self.excel_data: Dict[str, pd.DataFrame] = {}
    
    def import_excel(self, file_path: str, index_column: str = None) -> str:
        """
        导入Excel文件
        
        Args:
            file_path: Excel文件路径
            index_column: 索引列名，如果为None则使用行号作为索引
            
        Returns:
            导入ID
        """
        try:
            # 生成唯一导入ID
            import_id = str(uuid.uuid4())
            
            # 读取Excel文件
            self.log_manager.info(f"正在导入Excel文件: {file_path}")
            df = pd.read_excel(file_path)
            
            # 设置索引列
            if index_column and index_column in df.columns:
                df.set_index(index_column, inplace=True)
                self.log_manager.info(f"使用列 '{index_column}' 作为索引")
            else:
                # 如果没有指定索引列，使用行号作为索引
                df.index.name = 'Row_Index'
                self.log_manager.info("使用行号作为索引")
            
            # 保存到临时目录
            temp_file = self.base_dir / "imports" / f"{import_id}.xlsx"
            df.to_excel(temp_file, index=True)
            
            # 存储数据
            self.excel_data[import_id] = df
            
            self.log_manager.info(f"Excel文件导入成功，导入ID: {import_id}")
            self.log_manager.info(f"数据形状: {df.shape}")
            self.log_manager.info(f"列名: {list(df.columns)}")
            
            return import_id
            
        except Exception as e:
            self.log_manager.error(f"导入Excel文件失败: {e}")
            raise
    
    def get_excel_info(self, import_id: str) -> Dict[str, Any]:
        """
        获取导入的Excel文件信息
        
        Args:
            import_id: 导入ID
            
        Returns:
            Excel文件信息字典
        """
        if import_id not in self.excel_data:
            raise ValueError(f"导入ID不存在: {import_id}")
        
        df = self.excel_data[import_id]
        
        return {
            "import_id": import_id,
            "shape": [int(df.shape[0]), int(df.shape[1])],
            "columns": [str(c) for c in list(df.columns)],
            "index_name": str(df.index.name) if df.index.name is not None else "",
            "sample_data": df.head(5).fillna("").astype(str).to_dict('records'),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    
    def create_parsing_rule(self, source_column: str, target_columns: List[str], prompt: str) -> ParsingRule:
        """
        创建解析规则
        
        Args:
            source_column: 源列名
            target_columns: 目标列名列表
            prompt: 解析提示词
            
        Returns:
            解析规则对象
        """
        return ParsingRule(
            source_column=source_column,
            target_columns=target_columns,
            prompt=prompt
        )
    
    def start_processing_task(self, import_id: str, parsing_rules: List[ParsingRule], threads: int = 1, checkpoint_every: int = 50, name: str = "") -> str:
        """
        启动异步处理任务
        """
        if import_id not in self.excel_data:
            raise ValueError(f"导入ID不存在: {import_id}")
        task_id = str(uuid.uuid4())
        output_filename = f"processed_{import_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_file = str(self.base_dir / "exports" / output_filename)
        partial_output_file = str(self.base_dir / "temp" / f"{task_id}_partial.pkl")
        progress_file = str(self.base_dir / "temp" / f"{task_id}_progress.json")
        task = ProcessingTask(
            task_id=task_id,
            input_file=str(self.base_dir / "imports" / f"{import_id}.xlsx"),
            output_file=output_file,
            parsing_rules=parsing_rules,
            status=TaskStatus.PENDING,
            progress=0.0,
            total_records=len(self.excel_data[import_id]),
            processed_records=0,
            start_time=datetime.now(),
            threads=max(1, int(threads)),
            checkpoint_every=max(1, int(checkpoint_every)),
            partial_output_file=partial_output_file,
            progress_file=progress_file,
            name=str(name or "")
        )
        with self._tasks_lock:
            self.tasks[task_id] = task
        thread = threading.Thread(target=self._process_task, args=(task_id,))
        thread.daemon = True
        thread.start()
        self.log_manager.info(f"处理任务已启动，任务ID: {task_id}")
        return task_id
    
    def _save_progress(self, task: ProcessingTask, result_df: pd.DataFrame):
        """保存中间结果与进度文件"""
        try:
            # 保存部分结果
            result_df.to_pickle(task.partial_output_file)
            # 保存进度元数据
            meta = {
                "task_id": task.task_id,
                "input_file": task.input_file,
                "output_file": task.output_file,
                "partial_output_file": task.partial_output_file,
                "progress_file": task.progress_file,
                "status": task.status.value,
                "total_records": task.total_records,
                "processed_records": task.processed_records,
                "threads": task.threads,
                                 "checkpoint_every": task.checkpoint_every,
                 "name": task.name,
                 "parsing_rules": [
                     {
                         "source_column": r.source_column,
                         "target_columns": r.target_columns,
                         "prompt": r.prompt,
                         "rule_id": r.rule_id,
                     }
                     for r in task.parsing_rules
                 ],
                 "timestamp": datetime.now().isoformat(),
             }
            with open(task.progress_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False)
        except Exception as e:
            self.log_manager.error(f"保存进度失败: {e}")
    
    def _load_progress(self, task: ProcessingTask) -> Optional[pd.DataFrame]:
        """加载进度与部分结果，如存在则返回部分结果DataFrame"""
        try:
            if task.partial_output_file and os.path.exists(task.partial_output_file):
                return pd.read_pickle(task.partial_output_file)
        except Exception as e:
            self.log_manager.error(f"加载部分结果失败: {e}")
        return None
    
    def _process_task(self, task_id: str):
        task = self.tasks[task_id]
        
        # 为任务创建独立的日志管理器
        task_log_manager = LogManager(task_id)
        
        try:
            task.status = TaskStatus.PROCESSING
            task_log_manager.info(f"开始处理任务: {task_id}")
            
            # 加载原始数据
            df = pd.read_excel(task.input_file)
            task_log_manager.info(f"加载Excel文件: {task.input_file}, 记录数: {len(df)}")
            
            # 初始化结果DataFrame（包含原始列）
            result_df = self._load_progress(task)
            if result_df is None:
                result_df = df.copy()
                # 添加目标列
                for rule in task.parsing_rules:
                    for target_col in rule.target_columns:
                        if target_col not in result_df.columns:
                            result_df[target_col] = ''
                task.processed_records = 0
                task_log_manager.info(f"初始化结果DataFrame，添加目标列: {[col for rule in task.parsing_rules for col in rule.target_columns]}")
            else:
                # 已有部分结果，推断已处理数量
                task.processed_records = min(len(result_df) - df.shape[0], 0) or 0  # 兜底，不影响继续处理
                # 简化：根据进度文件字段为准
                if task.progress_file and os.path.exists(task.progress_file):
                    try:
                        meta = json.load(open(task.progress_file, 'r'))
                        task.processed_records = int(meta.get('processed_records', 0))
                    except Exception:
                        pass
                task_log_manager.info(f"从检查点恢复，已处理记录数: {task.processed_records}")
            
            # 分批参数
            batch_size = 10
            total_len = len(df)
            # 从已处理记录继续
            start_batch = task.processed_records // batch_size
            task_log_manager.info(f"开始批次处理，总记录数: {total_len}, 批次大小: {batch_size}, 起始批次: {start_batch}")
            
            # 执行批次
            for batch_idx in range(start_batch, (total_len + batch_size - 1) // batch_size):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, total_len)
                batch_df = df.iloc[start_idx:end_idx]
                
                # 记录批次开始
                task_log_manager.log_batch_start(
                    batch_num=batch_idx + 1,
                    batch_size=len(batch_df),
                    total_records=total_len,
                    start_index=start_idx,
                    end_index=end_idx
                )
                
                batch_start_time = time.time()
                
                # 并行按规则处理
                aggregated_results: Dict[Any, Dict[str, Any]] = {}
                rule_errors = []
                
                with ThreadPoolExecutor(max_workers=task.threads) as executor:
                    futures = {
                        executor.submit(self._process_rule_on_batch, rule, batch_df, task_log_manager): rule
                        for rule in task.parsing_rules
                    }
                    for fut in as_completed(futures):
                        rule = futures[fut]
                        try:
                            rule_result = fut.result()
                            # 合并结果到 aggregated_results
                            for i, (idx, _) in enumerate(batch_df.iterrows()):
                                if i < len(rule_result):
                                    if idx not in aggregated_results:
                                        aggregated_results[idx] = {}
                                    aggregated_results[idx].update(rule_result[i])
                        except Exception as e:
                            error_msg = f"规则 {rule.rule_id} 处理失败: {e}"
                            task_log_manager.error(error_msg)
                            rule_errors.append(error_msg)
                            for idx in batch_df.index:
                                if idx not in aggregated_results:
                                    aggregated_results[idx] = {}
                                for target_col in rule.target_columns:
                                    aggregated_results[idx][target_col] = ''
                
                # 写入结果
                for i, (idx, _) in enumerate(batch_df.iterrows()):
                    global_pos = start_idx + i
                    row_result = aggregated_results.get(idx, {})
                    for k, v in row_result.items():
                        if k in result_df.columns:
                            result_df.iloc[global_pos, result_df.columns.get_loc(k)] = v
                
                # 计算批次处理时间
                batch_processing_time = time.time() - batch_start_time
                success_count = len([r for r in aggregated_results.values() if any(r.values())])
                
                # 记录批次完成
                task_log_manager.log_batch_complete(
                    batch_num=batch_idx + 1,
                    success_count=success_count,
                    total_count=len(batch_df),
                    processing_time=batch_processing_time,
                    errors=rule_errors
                )
                
                # 更新进度
                task.processed_records = end_idx
                task.progress = (task.processed_records / task.total_records) * 100.0
                
                # 记录任务进度
                task_log_manager.log_task_progress(
                    task_id=task_id,
                    processed_records=task.processed_records,
                    total_records=task.total_records,
                    progress_percentage=task.progress,
                    current_status=task.status.value
                )
                
                # 检查点保存
                if (end_idx % task.checkpoint_every == 0) or (end_idx == total_len):
                    self._save_progress(task, result_df)
                    task_log_manager.info(f"已保存检查点 {end_idx}/{total_len}")
            # 完成：导出Excel
            result_df.to_excel(task.output_file, index=True)
            task.status = TaskStatus.COMPLETED
            task.progress = 100.0
            task.end_time = datetime.now()
            self._save_progress(task, result_df)
            task_log_manager.info(f"任务已完成，结果文件: {task.output_file}")
        except Exception as e:
            task_log_manager.error(f"任务处理失败: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.end_time = datetime.now()
            # 保存失败时的进度
            try:
                self._save_progress(task, result_df if 'result_df' in locals() else pd.read_excel(task.input_file))
            except Exception:
                pass
    
    def _build_batch_prompt(self, rule: ParsingRule, batch_df: pd.DataFrame) -> str:
        """
        构建批量处理的提示词
        
        Args:
            rule: 解析规则
            batch_df: 批次数据
            
        Returns:
            提示词字符串
        """
        prompt = f"""请根据以下规则从病例记录中提取信息：

**提取规则：**
{rule.prompt}

**目标列：**
{', '.join(rule.target_columns)}

**数据格式要求：**
- 输出为标准JSON数组，每个对象包含以下字段：{', '.join(rule.target_columns)}
- 如果某个字段在原文中未找到，请将该字段设为空字符串
- 严格按照JSON格式输出，确保语法正确

**待处理数据：**
"""
        
        for i, (idx, row) in enumerate(batch_df.iterrows()):
            source_value = str(row[rule.source_column])
            prompt += f"记录 {i+1} (索引: {idx}):\n{source_value}\n\n"
        
        prompt += """**输出格式示例：**
```json
[
  {
    "字段1": "值1",
    "字段2": "值2"
  }
]
```

请严格按照上述格式输出JSON数组。"""
        
        return prompt
    
    def _call_api(self, prompt: str, log_manager: LogManager = None, rule_id: str = None, batch_info: Dict[str, Any] = None) -> str:
        """
        调用大模型API
        
        Args:
            prompt: 提示词
            log_manager: 日志管理器
            rule_id: 规则ID
            batch_info: 批次信息
            
        Returns:
            API响应内容
        """
        from config import Config
        
        # 记录API请求
        if log_manager and rule_id:
            log_manager.log_llm_request(prompt, rule_id, batch_info)
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            **Config.get_api_payload_template()
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                error_msg = f"API请求失败，状态码: {response.status_code}, 错误信息: {response.text}"
                if log_manager and rule_id:
                    log_manager.log_llm_response("", rule_id, batch_info, time.time() - start_time, False)
                raise Exception(error_msg)
            
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 记录API响应
            if log_manager and rule_id:
                log_manager.log_llm_response(content, rule_id, batch_info, time.time() - start_time, True)
            
            return content
            
        except Exception as e:
            # 记录API调用异常
            if log_manager and rule_id:
                log_manager.log_llm_response(str(e), rule_id, batch_info, time.time() - start_time, False)
            raise
    
    def _parse_api_response(self, response: str, target_columns: List[str]) -> List[Dict[str, Any]]:
        """
        解析API响应
        
        Args:
            response: API响应内容
            target_columns: 目标列名列表
            
        Returns:
            解析结果列表
        """
        try:
            # 查找JSON数组的开始和结束位置
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                parsed_data = json.loads(json_str)
                
                # 验证数据结构
                if not isinstance(parsed_data, list):
                    raise ValueError("API响应不是有效的JSON数组")
                
                # 确保每个对象都包含目标列
                for item in parsed_data:
                    if not isinstance(item, dict):
                        continue
                    for col in target_columns:
                        if col not in item:
                            item[col] = ''
                
                return parsed_data
            else:
                # 注意：这里没有log_manager，使用默认的日志记录
                print(f"警告: 未找到有效的JSON数组格式")
                return [{} for _ in range(len(target_columns))]
                
        except json.JSONDecodeError as e:
            # 注意：这里没有log_manager，使用默认的日志记录
            print(f"错误: JSON解析失败: {e}")
            print(f"原始响应: {response}")
            return [{} for _ in range(len(target_columns))]

    def _process_rule_on_batch(self, rule: ParsingRule, batch_df: pd.DataFrame, log_manager: LogManager = None) -> List[Dict[str, Any]]:
        """对单条规则处理一批数据（供并发执行）"""
        try:
            prompt = self._build_batch_prompt(rule, batch_df)
            
            # 构建批次信息
            batch_info = {
                'batch_size': len(batch_df),
                'source_column': rule.source_column,
                'target_columns': rule.target_columns,
                'record_indices': list(batch_df.index)
            }
            
            api_response = self._call_api(prompt, log_manager, rule.rule_id, batch_info)
            parsed_results = self._parse_api_response(api_response, rule.target_columns)
            
            # 记录规则处理结果
            if log_manager:
                log_manager.log_rule_processing(
                    rule_id=rule.rule_id,
                    source_column=rule.source_column,
                    target_columns=rule.target_columns,
                    record_count=len(batch_df),
                    success=True
                )
            
            return parsed_results
            
        except Exception as e:
            # 记录规则处理失败
            if log_manager:
                log_manager.log_rule_processing(
                    rule_id=rule.rule_id,
                    source_column=rule.source_column,
                    target_columns=rule.target_columns,
                    record_count=len(batch_df),
                    success=False,
                    error_message=str(e)
                )
            raise

    def get_task_status(self, task_id: str) -> Optional[ProcessingTask]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """列出所有任务（包含磁盘上的历史任务）"""
        tasks_info: List[Dict[str, Any]] = []
        # 内存任务
        with self._tasks_lock:
            for task in self.tasks.values():
                tasks_info.append({
                    "task_id": task.task_id,
                    "name": task.name,
                    "status": task.status.value,
                    "progress": task.progress,
                    "total_records": task.total_records,
                    "processed_records": task.processed_records,
                    "start_time": task.start_time.isoformat(),
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    "error_message": task.error_message
                })
        # 磁盘历史任务
        temp_dir = self.base_dir / "temp"
        for file in temp_dir.glob("*_progress.json"):
            try:
                meta = json.load(open(file, 'r'))
                # 去重：内存已有则跳过
                if any(t["task_id"] == meta.get("task_id") for t in tasks_info):
                    continue
                tasks_info.append({
                    "task_id": meta.get("task_id"),
                    "name": meta.get("name", ""),
                    "status": meta.get("status"),
                    "progress": round(100.0 * float(meta.get("processed_records", 0)) / float(meta.get("total_records", 1)), 2),
                    "total_records": meta.get("total_records"),
                    "processed_records": meta.get("processed_records"),
                    "start_time": meta.get("timestamp"),
                    "end_time": None,
                    "error_message": None
                })
            except Exception:
                continue
        return tasks_info
    
    def restart_task(self, task_id: str) -> str:
        """从进度文件恢复并重启任务"""
        # 若内存中存在且未完成，直接返回
        with self._tasks_lock:
            if task_id in self.tasks and self.tasks[task_id].status == TaskStatus.PROCESSING:
                return task_id
        progress_file = self.base_dir / "temp" / f"{task_id}_progress.json"
        if not progress_file.exists():
            raise ValueError("未找到可恢复的进度文件")
        meta = json.load(open(progress_file, 'r'))
        # 重建规则
        rules = [ParsingRule(r["source_column"], r["target_columns"], r["prompt"], r.get("rule_id")) for r in meta.get("parsing_rules", [])]
        task = ProcessingTask(
            task_id=task_id,
            input_file=meta["input_file"],
            output_file=meta["output_file"],
            parsing_rules=rules,
            status=TaskStatus.PENDING,
            progress=round(100.0 * float(meta.get("processed_records", 0)) / float(meta.get("total_records", 1)), 2),
            total_records=int(meta.get("total_records", 0)),
            processed_records=int(meta.get("processed_records", 0)),
            start_time=datetime.now(),
            threads=int(meta.get("threads", 1)),
            checkpoint_every=int(meta.get("checkpoint_every", 50)),
            partial_output_file=meta.get("partial_output_file"),
            progress_file=str(progress_file),
            name=meta.get("name", "")
        )
        with self._tasks_lock:
            self.tasks[task_id] = task
        thread = threading.Thread(target=self._process_task, args=(task_id,))
        thread.daemon = True
        thread.start()
        return task_id
    
    def download_partial_result(self, task_id: str) -> Optional[str]:
        """导出当前任务已处理的部分结果为Excel并返回路径。若完整结果已生成则返回完整结果。"""
        # 若任务存在且已完成，直接返回完整结果
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.COMPLETED and os.path.exists(task.output_file):
            return task.output_file
        # 尝试从进度文件读取部分结果
        progress_file_path = self.base_dir / "temp" / f"{task_id}_progress.json"
        partial_file_path = self.base_dir / "temp" / f"{task_id}_partial.pkl"
        # 若内存任务存在也尝试其部分结果路径
        if task and task.partial_output_file:
            partial_file_path = Path(task.partial_output_file)
        if os.path.exists(str(partial_file_path)):
            try:
                df = pd.read_pickle(str(partial_file_path))
                export_path = self.base_dir / "exports" / f"partial_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(str(export_path), index=True)
                return str(export_path)
            except Exception:
                return None
        # 如果没有部分结果但完整结果存在
        if task and os.path.exists(task.output_file):
            return task.output_file
        # 兜底：若进度文件存在但没有partial，则返回None
        if os.path.exists(str(progress_file_path)):
            return None
        return None

    def download_result(self, task_id: str) -> Optional[str]:
        """
        下载处理结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            结果文件路径，如果任务未完成则返回None
        """
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.COMPLETED:
            return None
        
        if os.path.exists(task.output_file):
            return task.output_file
        else:
            return None

def main():
    """主函数 - 演示用法"""
    print("=" * 60)
    print("Excel半结构化数据解析工具")
    print("=" * 60)
    
    # 配置
    api_key = "gJrVzbTcTtitntvY5sdNE2tMHdM2O8AH8j9l5q48TV3gJNkh"
    
    # 创建解析器
    parser = ExcelStructuredParser(api_key)
    
    # 示例用法
    print("\n1. 导入Excel文件")
    print("2. 创建解析规则")
    print("3. 启动处理任务")
    print("4. 监控任务进度")
    print("5. 下载处理结果")
    
    # 这里可以添加交互式操作或API接口
    print("\n工具已初始化完成，可以通过API接口或修改代码来使用具体功能")

if __name__ == "__main__":
    main() 