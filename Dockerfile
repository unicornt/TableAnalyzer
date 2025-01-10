# 使用官方的 Python 基础镜像
FROM python:3.9-slim

# 安装所需的 Python 包
RUN pip install --no-cache-dir pandas duckdb openpyxl matplotlib jinja2 openai flask

RUN apt update && apt upgrade
RUN apt install -y fonts-noto-cjk
RUN apt install -y fontconfig

RUN fc-cache -fv
RUN pip install --no-cache-dir python-magic
RUN apt-get install -y libmagic1
# 设置工作目录
WORKDIR /app

COPY ./api.py /app
COPY ./NotoSansCJK-Regular.ttc /app

# 设置默认命令来运行 Python 脚本
CMD ["python", "api.py"]