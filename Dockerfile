# 基础镜像
# 1. 基础镜像
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 复制所有代码到容器
COPY . .

# 4. 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 5. 创建图片保存路径
RUN mkdir -p assets/images temp_uploads

# 6. 默认启动命令：运行主程序 main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

