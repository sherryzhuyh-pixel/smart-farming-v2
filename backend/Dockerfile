# AI智慧养殖系统V2.0 - Render部署Docker镜像
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 创建数据目录（Render磁盘挂载点）
RUN mkdir -p /data && chmod 777 /data

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

# 暴露端口
EXPOSE 8000

# 启动命令：Render使用PORT环境变量
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
