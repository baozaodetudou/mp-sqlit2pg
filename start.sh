#!/bin/bash
# 启动SQLite到PostgreSQL迁移工具

echo "正在启动SQLite到PostgreSQL迁移工具..."

# 检查是否安装了必要的依赖
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ $MAJOR_VERSION -lt 3 ] || [ $MAJOR_VERSION -eq 3 -a $MINOR_VERSION -lt 12 ]; then
    echo "警告: 推荐使用Python 3.12或更高版本，当前版本: $PYTHON_VERSION"
fi

if ! command -v pip &> /dev/null; then
    echo "错误: 未找到pip"
    exit 1
fi

# 检查并安装依赖
if [ -f "requirements.txt" ]; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

# 检查是否安装了pgloader
if ! command -v pgloader &> /dev/null; then
    echo "警告: 未找到pgloader，迁移功能可能无法正常工作"
    echo "请安装pgloader:"
    echo "  Ubuntu/Debian: sudo apt install pgloader"
    echo "  CentOS/RHEL: sudo yum install pgloader"
    echo "  macOS: brew install pgloader"
fi

# 检查是否安装了PostgreSQL客户端
if ! command -v pg_dump &> /dev/null; then
    echo "警告: 未找到PostgreSQL客户端工具，备份和恢复功能可能无法正常工作"
    echo "请安装PostgreSQL客户端:"
    echo "  Ubuntu/Debian: sudo apt install postgresql-client"
    echo "  CentOS/RHEL: sudo yum install postgresql-client"
    echo "  macOS: brew install libpq"
fi

# 启动应用
echo "正在启动应用..."
echo "应用将在 http://localhost:5055 上运行"
echo "API文档可在 http://localhost:5055/docs 访问"
echo "按 Ctrl+C 停止应用"

uvicorn app:app --host 0.0.0.0 --port 5055