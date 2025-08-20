# SQLite到PostgreSQL迁移工具

这是一个用于将SQLite数据库迁移到PostgreSQL数据库的Web工具，同时支持PostgreSQL数据库的备份和恢复功能。

## 功能特性

1. **数据库迁移**：将SQLite数据库迁移到PostgreSQL
2. **数据库备份**：导出PostgreSQL数据库为SQL文件
3. **数据库恢复**：从SQL文件恢复PostgreSQL数据库

## 安装依赖

确保您使用的是Python 3.12或更高版本：

```bash
pip install -r requirements.txt
```

## 安装pgloader

在使用迁移功能之前，需要安装pgloader工具：

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install pgloader
```

### CentOS/RHEL:
```bash
sudo yum install pgloader
```

### macOS:
```bash
brew install pgloader
```

## 运行应用

### 使用Python直接运行：
```bash
python app.py
```

### 使用uvicorn运行：
```bash
uvicorn app:app --host 0.0.0.0 --port 5055
```

### 使用Docker运行：
```bash
# 构建并运行Docker镜像
docker build -t sqlite-to-postgres .
docker run -p 5055:5055 sqlite-to-postgres

# 或者使用docker-compose（推荐）
docker-compose up -d
```

应用将在 `http://localhost:5055` 上运行。FastAPI还提供了交互式API文档，可以在 `http://localhost:5055/docs` 访问。

### Docker部署说明

Docker镜像已优化以支持PostgreSQL 17.5及以下版本，并包含所有必要的依赖项：
- Python 3.12
- PostgreSQL客户端工具
- pgloader (通过包管理器安装)
- 所有Python依赖

使用docker-compose可以同时部署应用和PostgreSQL数据库。

### ARM平台支持

应用支持ARM平台部署：
```bash
# 构建ARM64镜像
docker build --platform linux/arm64 -t sqlite-to-postgres:arm64 .

# 使用ARM64 docker-compose文件
docker-compose -f docker-compose.arm64.yml up -d
```

也可以使用build.sh脚本进行交叉编译构建。

## 使用方法

1. 在PostgreSQL中创建数据库和用户（如果尚未创建）：
   ```sql
   CREATE USER moviepilot WITH PASSWORD 'moviepilot';
   CREATE DATABASE moviepilot;
   GRANT ALL PRIVILEGES ON DATABASE moviepilot TO moviepilot;
   ```

2. 打开浏览器访问 `http://localhost:5055`

3. 配置PostgreSQL数据库连接信息：
   - 主机地址：PostgreSQL服务器地址（默认localhost）
   - 端口：PostgreSQL端口（默认5432）
   - 数据库名：目标数据库名
   - 用户名：PostgreSQL用户名
   - 密码：PostgreSQL密码

4. 使用迁移功能：
   - 选择要迁移的SQLite文件
   - 点击"迁移数据库"按钮

5. 使用备份功能：
   - 点击"备份数据库"按钮下载备份文件

6. 使用恢复功能：
   - 选择备份的SQL文件
   - 点击"恢复数据库"按钮

## 注意事项

1. 请确保PostgreSQL服务正在运行
2. 请确保提供的PostgreSQL用户具有足够的权限
3. 迁移前请备份原始数据
4. 大型数据库的迁移可能需要较长时间