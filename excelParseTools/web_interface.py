#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel半结构化数据解析工具 - Web界面
提供文件上传、规则配置、任务管理和结果下载功能
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, Blueprint
from flask_cors import CORS
import os
import json
import time
from datetime import datetime
from excel_structured_parser import ExcelStructuredParser, ParsingRule
from logger_manager import LogManager
import pandas as pd

app = Flask(__name__)
CORS(app)

from config import get_config

# 获取配置
config = get_config()
app.config.from_object(config)

# 创建带前缀的蓝图
bp = Blueprint('excel_tools', __name__, url_prefix='/excel-tools')

# 初始化解析器
parser = ExcelStructuredParser()

# 全局日志管理器
global_log_manager = LogManager()

@bp.route('/health')
def health():
    """健康检查接口"""
    return jsonify({"status": "ok", "service": "excel-parse-tools"}), 200

@bp.route('/')
def index():
    """主页"""
    return render_template('index.html')

@bp.route('/logs')
def logs_page():
    """日志管理页面"""
    return render_template('logs.html')

@bp.route('/tasks')
def tasks_page():
    """任务管理页面"""
    return render_template('tasks.html')

@bp.route('/best-practice')
def best_practice_page():
    """最佳实践页面"""
    return render_template('best_practice.html')

@bp.route('/docs/<doc_name>')
def get_document(doc_name):
    """获取文档内容"""
    import os
    from pathlib import Path
    
    # 安全的文档名称列表
    allowed_docs = ['INDEX', 'README', 'QUICK_START', 'BEST_PRACTICE', 'SUMMARY']
    
    if doc_name not in allowed_docs:
        return "文档不存在", 404
    
    # 构建文档路径
    base_dir = Path(__file__).parent
    doc_path = base_dir / f"{doc_name}.md"
    
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return f"读取文档失败: {str(e)}", 500

@bp.route('/download-sample')
def download_sample():
    """下载示例数据"""
    import os
    from pathlib import Path
    
    base_dir = Path(__file__).parent
    sample_file = base_dir / "excel_parser_data" / "imports" / "best_practice_sample_50.xlsx"
    
    if os.path.exists(sample_file):
        return send_file(sample_file, as_attachment=True, download_name="best_practice_sample_50.xlsx")
    else:
        return jsonify({'error': '示例文件不存在'}), 404

@bp.route('/view-template')
def view_template():
    """查看规则模板"""
    import os
    from pathlib import Path
    
    base_dir = Path(__file__).parent
    template_file = base_dir / "rule_templates" / "medical_record_rules.json"
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'application/json; charset=utf-8'}
    except Exception as e:
        return jsonify({'error': f'读取模板失败: {str(e)}'}), 500

@bp.route('/upload', methods=['POST'])
def upload_file():
    """上传Excel文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': '只支持Excel文件格式(.xlsx, .xls)'}), 400
        
        # 保存文件
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join(str(parser.base_dir), "temp", filename)
        file.save(file_path)
        
        # 导入Excel
        index_column = request.form.get('index_column', None)
        if index_column == '':
            index_column = None
        
        import_id = parser.import_excel(file_path, index_column)
        
        # 获取Excel信息
        excel_info = parser.get_excel_info(import_id)
        
        return jsonify({
            'success': True,
            'import_id': import_id,
            'excel_info': excel_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/create_rule', methods=['POST'])
def create_rule():
    """创建解析规则"""
    try:
        data = request.json
        source_column = data.get('source_column')
        target_columns = data.get('target_columns', [])
        prompt = data.get('prompt')
        
        if not source_column or not target_columns or not prompt:
            return jsonify({'error': '缺少必要参数'}), 400
        
        rule = parser.create_parsing_rule(source_column, target_columns, prompt)
        
        return jsonify({
            'success': True,
            'rule': {
                'rule_id': rule.rule_id,
                'source_column': rule.source_column,
                'target_columns': rule.target_columns,
                'prompt': rule.prompt
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/start_task', methods=['POST'])
def start_task():
    """启动处理任务，支持线程数与检查点配置"""
    try:
        data = request.json or {}
        import_id = data.get('import_id')
        rules_data = data.get('rules', [])
        threads = int(data.get('threads', 1))
        checkpoint_every = int(data.get('checkpoint_every', 50))
        
        if not import_id or not rules_data:
            return jsonify({'error': '缺少必要参数'}), 400

        # 安全参数校验
        if threads < 1 or threads > 8:
            return jsonify({'error': '线程数量必须在1-8之间'}), 400
        if checkpoint_every < 1 or checkpoint_every > 10000:
            return jsonify({'error': 'checkpoint_every 必须在1-10000之间'}), 400
        
        # 创建解析规则对象
        parsing_rules = []
        for rule_data in rules_data:
            rule = ParsingRule(
                source_column=rule_data['source_column'],
                target_columns=rule_data['target_columns'],
                prompt=rule_data['prompt'],
                rule_id=rule_data.get('rule_id')
            )
            parsing_rules.append(rule)
        
        # 启动任务
        task_id = parser.start_processing_task(import_id, parsing_rules, threads=threads, checkpoint_every=checkpoint_every)
        
        return jsonify({
            'success': True,
            'task_id': task_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/control', methods=['POST'])
def control_logging():
    """控制日志记录功能"""
    try:
        data = request.json or {}
        action = data.get('action')
        
        if action == 'enable_llm':
            global_log_manager.config.ENABLE_LLM_LOGGING = True
            return jsonify({'success': True, 'message': '大模型交互日志已启用'})
        elif action == 'disable_llm':
            global_log_manager.config.ENABLE_LLM_LOGGING = False
            return jsonify({'success': True, 'message': '大模型交互日志已禁用'})
        elif action == 'enable_batch':
            global_log_manager.config.ENABLE_BATCH_LOGGING = True
            return jsonify({'success': True, 'message': '批次处理日志已启用'})
        elif action == 'disable_batch':
            global_log_manager.config.ENABLE_BATCH_LOGGING = False
            return jsonify({'success': True, 'message': '批次处理日志已禁用'})
        elif action == 'enable_detailed':
            global_log_manager.config.ENABLE_DETAILED_LOGGING = True
            return jsonify({'success': True, 'message': '详细日志已启用'})
        elif action == 'disable_detailed':
            global_log_manager.config.ENABLE_DETAILED_LOGGING = False
            return jsonify({'success': True, 'message': '详细日志已禁用'})
        elif action == 'enable_api_requests':
            global_log_manager.config.LOG_API_REQUESTS = True
            return jsonify({'success': True, 'message': 'API请求日志已启用'})
        elif action == 'disable_api_requests':
            global_log_manager.config.LOG_API_REQUESTS = False
            return jsonify({'success': True, 'message': 'API请求日志已禁用'})
        elif action == 'enable_api_responses':
            global_log_manager.config.LOG_API_RESPONSES = True
            return jsonify({'success': True, 'message': 'API响应日志已启用'})
        elif action == 'disable_api_responses':
            global_log_manager.config.LOG_API_RESPONSES = False
            return jsonify({'success': True, 'message': 'API响应日志已禁用'})
        else:
            return jsonify({'error': '无效的操作'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/status')
def get_logging_status():
    """获取当前日志配置状态"""
    try:
        return jsonify({
            'enable_llm_logging': global_log_manager.config.ENABLE_LLM_LOGGING,
            'enable_batch_logging': global_log_manager.config.ENABLE_BATCH_LOGGING,
            'enable_detailed_logging': global_log_manager.config.ENABLE_DETAILED_LOGGING,
            'log_api_requests': global_log_manager.config.LOG_API_REQUESTS,
            'log_api_responses': global_log_manager.config.LOG_API_RESPONSES
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/view/<task_id>')
def view_task_logs(task_id):
    """查看指定任务的日志"""
    try:
        # 创建任务专用的日志管理器
        task_log_manager = LogManager(task_id)
        
        # 获取日志缓存
        logs = task_log_manager.get_log_cache()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'logs': logs,
            'summary': task_log_manager.get_log_summary()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/view')
def view_global_logs():
    """查看全局日志"""
    try:
        logs = global_log_manager.get_log_cache()
        
        return jsonify({
            'success': True,
            'logs': logs,
            'summary': global_log_manager.get_log_summary()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/export/<task_id>')
def export_task_logs(task_id):
    """导出指定任务的日志"""
    try:
        task_log_manager = LogManager(task_id)
        export_path = task_log_manager.export_logs()
        
        return jsonify({
            'success': True,
            'export_path': export_path,
            'message': '日志导出成功'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/export')
def export_global_logs():
    """导出全局日志"""
    try:
        export_path = global_log_manager.export_logs()
        
        return jsonify({
            'success': True,
            'export_path': export_path,
            'message': '日志导出成功'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/clear/<task_id>')
def clear_task_logs(task_id):
    """清空指定任务的日志缓存"""
    try:
        task_log_manager = LogManager(task_id)
        task_log_manager.clear_log_cache()
        
        return jsonify({
            'success': True,
            'message': f'任务 {task_id} 的日志缓存已清空'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/logs/clear')
def clear_global_logs():
    """清空全局日志缓存"""
    try:
        global_log_manager.clear_log_cache()
        
        return jsonify({
            'success': True,
            'message': '全局日志缓存已清空'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/restart/<task_id>', methods=['POST'])
def restart_task(task_id):
    """手动重启任务（断点续传）"""
    try:
        new_task_id = parser.restart_task(task_id)
        return jsonify({'success': True, 'task_id': new_task_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/task_status/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    try:
        task = parser.get_task_status(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        return jsonify({
            'task_id': task.task_id,
            'status': task.status.value,
            'progress': task.progress,
            'total_records': task.total_records,
            'processed_records': task.processed_records,
            'start_time': task.start_time.isoformat(),
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'error_message': task.error_message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/tasks_list')
def list_tasks():
    """列出所有任务（API）"""
    try:
        tasks = parser.list_tasks()
        return jsonify({
            'success': True,
            'tasks': tasks
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/delete_task/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务及其相关文件"""
    try:
        # 从内存中删除任务
        with parser._tasks_lock:
            if task_id in parser.tasks:
                task = parser.tasks[task_id]
                
                # 删除相关文件
                import os
                from pathlib import Path
                
                # 删除输出文件
                if task.output_file and os.path.exists(task.output_file):
                    try:
                        os.remove(task.output_file)
                    except:
                        pass
                
                # 删除部分结果文件
                if task.partial_output_file and os.path.exists(task.partial_output_file):
                    try:
                        os.remove(task.partial_output_file)
                    except:
                        pass
                
                # 删除进度文件
                if task.progress_file and os.path.exists(task.progress_file):
                    try:
                        os.remove(task.progress_file)
                    except:
                        pass
                
                # 从内存中删除
                del parser.tasks[task_id]
        
        # 删除磁盘上的进度文件（如果不在内存中）
        progress_file = parser.base_dir / "temp" / f"{task_id}_progress.json"
        if os.path.exists(progress_file):
            try:
                os.remove(progress_file)
            except:
                pass
        
        # 删除磁盘上的部分结果文件
        partial_file = parser.base_dir / "temp" / f"{task_id}_partial.pkl"
        if os.path.exists(partial_file):
            try:
                os.remove(partial_file)
            except:
                pass
        
        return jsonify({
            'success': True,
            'message': f'任务 {task_id} 已删除'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/download/<task_id>')
def download_result(task_id):
    """下载处理结果"""
    try:
        file_path = parser.download_result(task_id)
        if not file_path:
            return jsonify({'error': '任务未完成或文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/excel_info/<import_id>')
def get_excel_info(import_id):
    """获取Excel文件信息"""
    try:
        excel_info = parser.get_excel_info(import_id)
        return jsonify({
            'success': True,
            'excel_info': excel_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 新增：设置/重置索引列
@bp.route('/set_index', methods=['POST'])
def set_index():
    """为已导入的数据设置索引列（支持恢复为行号索引）"""
    try:
        data = request.json or {}
        import_id = data.get('import_id')
        index_column = data.get('index_column')  # 可以为''/None 表示使用行号
        if not import_id:
            return jsonify({'error': '缺少 import_id'}), 400
        # 读取当前DataFrame
        if import_id not in parser.excel_data:
            return jsonify({'error': '导入ID不存在'}), 404
        df = parser.excel_data[import_id]
        # 恢复索引为列，确保可以再次选择
        df = df.reset_index()
        # 如果指定了索引列
        if index_column:
            if index_column not in df.columns:
                return jsonify({'error': f'索引列不存在: {index_column}'}), 400
            df = df.set_index(index_column)
        else:
            # 使用行号作为索引
            df = df.reset_index(drop=True)
            df.index.name = 'Row_Index'
        # 保存并更新内存
        parser.excel_data[import_id] = df
        # 覆盖导入副本，保持与内存一致
        save_path = os.path.join(str(parser.base_dir), 'imports', f'{import_id}.xlsx')
        df.to_excel(save_path, index=True)
        # 返回最新excel信息
        info = parser.get_excel_info(import_id)
        return jsonify({'success': True, 'excel_info': info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 注册蓝图
app.register_blueprint(bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 