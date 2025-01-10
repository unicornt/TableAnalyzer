# 使用官方的 Python 基础镜像
FROM python:3.9-slim

# 安装所需的 Python 包
RUN pip install --no-cache-dir pandas duckdb openpyxl matplotlib jinja2 openai flask

RUN apt update && apt upgrade
RUN apt install -y fonts-noto-cjk
RUN apt install -y fontconfig

RUN fc-cache -fv
# 设置工作目录
WORKDIR /app

# 复制当前目录内容到工作目录
COPY . /app

# 设置默认命令来运行 Python 脚本
CMD ["python", "api.py"]