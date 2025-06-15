# Dockerfile.wine
FROM python:3.13.0-slim

# 安装 Wine 和必要的依赖
RUN apt-get update && apt-get install -y wine winetricks && rm -rf /var/lib/apt/lists/*

# 设置 Wine 环境
RUN wineboot --init && winetricks python3 && winetricks pywin32

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install -r requirements.txt pyinstaller

# 创建工作目录
WORKDIR /app
COPY . /app

# 构建命令
CMD ["wine", "python", "-m", "PyInstaller", "--onefile", "--windowed", "--target-arch=x86_64", "telegram_gui.py"]
