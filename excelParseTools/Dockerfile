# Excel 解析工具 Dockerfile
FROM registry.cn-shanghai.aliyuncs.com/hxzh_dev/hxzh-python:3.11

WORKDIR /app

# 安装缺失的依赖
RUN pip install --no-cache-dir openpyxl flask flask-cors

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/logs /app/excel_parser_data/temp /app/excel_parser_data/imports /app/excel_parser_data/exports

# 暴露端口
EXPOSE 5001

# 启动命令
CMD ["python", "run.py"]

