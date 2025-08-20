#!/bin/bash

# SQLite到PostgreSQL迁移工具构建脚本

set -e

echo "SQLite到PostgreSQL迁移工具构建脚本"
echo "==================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: 未找到Docker，请先安装Docker"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: 未找到docker-compose，请先安装docker-compose"
    exit 1
fi

# 显示选项
echo "请选择操作:"
echo "1) 构建Docker镜像 (x86_64)"
echo "2) 构建Docker镜像 (ARM64)"
echo "3) 构建Docker镜像 (交叉编译)"
echo "4) 启动服务 (仅应用)"
echo "5) 启动服务 (应用 + PostgreSQL)"
echo "6) 停止服务"
echo "7) 查看日志"
echo "8) 重新构建并启动 (应用 + PostgreSQL)"

read -p "请输入选项 (1-8): " choice

case $choice in
    1)
        echo "正在构建Docker镜像 (x86_64)..."
        docker build -t baozaodetudou/sqlite-to-postgres:amd64 .
        echo "Docker镜像构建完成"
        ;;
    2)
        echo "正在构建Docker镜像 (ARM64)..."
        docker build --platform linux/arm64 -t baozaodetudou/sqlite-to-postgres:arm64 .
        echo "ARM64 Docker镜像构建完成"
        ;;
    3)
        echo "请选择交叉编译目标平台:"
        echo "1) ARM64"
        echo "2) ARM/v7"
        echo "3) 多平台构建"
        read -p "请输入选项 (1-3): " platform_choice
        
        case $platform_choice in
            1)
                echo "正在构建ARM64镜像..."
                docker buildx build --platform linux/arm64 -t baozaodetudou/sqlite-to-postgres:arm64 .
                echo "ARM64镜像构建完成"
                ;;
            2)
                echo "正在构建ARM/v7镜像..."
                docker buildx build --platform linux/arm/v7 -t baozaodetudou/sqlite-to-postgres:armv7 .
                echo "ARM/v7镜像构建完成"
                ;;
            3)
                echo "正在构建多平台镜像..."
                DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64,linux/arm64 -t baozaodetudou/sqlite-to-postgres:latest --push .
                echo "多平台镜像构建完成"
                ;;
            *)
                echo "无效选项"
                exit 1
                ;;
        esac
        ;;
    4)
        echo "正在启动服务 (仅应用)..."
        docker run -d -p 5055:5055 --name baozaodetudou/sqlite-to-postgres sqlite-to-postgres
        echo "服务已启动，访问地址: http://localhost:5055"
        ;;
    5)
        echo "正在启动服务 (应用 + PostgreSQL)..."
        docker-compose up -d
        echo "服务已启动"
        echo "应用访问地址: http://localhost:5055"
        echo "PostgreSQL地址: localhost:5432"
        ;;
    6)
        echo "正在停止服务..."
        docker-compose down
        echo "服务已停止"
        ;;
    7)
        echo "查看日志:"
        docker-compose logs -f
        ;;
    8)
        echo "正在重新构建并启动服务..."
        docker-compose down
        docker build -t sqlite-to-postgres .
        docker-compose up -d
        echo "服务已重新构建并启动"
        echo "应用访问地址: http://localhost:5055"
        echo "PostgreSQL地址: localhost:5432"
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac