# AI 模型对比服务 Dockerfile
FROM registry.cn-shanghai.aliyuncs.com/hxzh_dev/hxzh-python:3.11

WORKDIR /app

# 安装缺失的依赖（jinja2 基础镜像已有，这里指定版本确保兼容）
RUN pip install --no-cache-dir pillow python-multipart jinja2

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

