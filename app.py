from fastapi import FastAPI, File, UploadFile, Form, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
import os
import subprocess
import time
from typing import Optional
import sqlite3
import psycopg2
import json

# 配置文件路径
CONFIG_FILE = "config.json"
app = FastAPI(title="SQLite to PostgreSQL Migration Tool")

# 确保配置文件存在
def ensure_config_file():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "pg_host": "localhost",
            "pg_port": "5432",
            "pg_database": "moviepilot",
            "pg_user": "moviepilot",
            "pg_password": "moviepilot"
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)

# 读取配置
def load_config():
    ensure_config_file()
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "pg_host": "localhost",
            "pg_port": "5432",
            "pg_database": "moviepilot",
            "pg_user": "moviepilot",
            "pg_password": "moviepilot"
        }

# 保存配置
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


@app.get("/config")
async def get_config():
    """获取保存的配置"""
    config = load_config()
    return JSONResponse(content=config)


@app.post("/save-config")
async def save_config_endpoint(
    pg_host: str = Form("localhost"),
    pg_port: str = Form("5432"),
    pg_database: str = Form("moviepilot"),
    pg_user: str = Form("moviepilot"),
    pg_password: str = Form("moviepilot")
):
    """保存配置"""
    config = {
        "pg_host": pg_host,
        "pg_port": pg_port,
        "pg_database": pg_database,
        "pg_user": pg_user,
        "pg_password": pg_password
    }
    save_config(config)
    return JSONResponse(content={"success": True, "message": "配置已保存"})



# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保目录存在
os.makedirs('uploads', exist_ok=True)
os.makedirs('exports', exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/test-postgresql")
async def test_postgresql_connection(
    pg_host: str = Form("localhost"),
    pg_port: str = Form("5432"),
    pg_database: str = Form("moviepilot"),
    pg_user: str = Form("moviepilot"),
    pg_password: str = Form("moviepilot")
):
    """测试PostgreSQL数据库连接"""
    try:
        # 创建数据库连接
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=pg_user,
            password=pg_password
        )
        
        # 获取数据库信息
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return JSONResponse(content={
            "success": True, 
            "message": f"连接成功",
            "version": version
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False, 
            "error": f"连接失败: {str(e)}"
        }, status_code=400)


@app.post("/validate-sqlite")
async def validate_sqlite_file(sqlite_file: UploadFile = File(...)):
    """验证SQLite文件"""
    try:
        # 保存临时文件
        filename = f"temp_{sqlite_file.filename}"
        filepath = os.path.join('uploads', filename)
        
        with open(filepath, 'wb') as f:
            content = await sqlite_file.read()
            f.write(content)
        
        # 验证SQLite文件
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        # 检查是否有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # 获取数据库信息
        cursor.execute("PRAGMA database_list")
        db_info = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 删除临时文件
        os.remove(filepath)
        
        return JSONResponse(content={
            "success": True,
            "message": f"SQLite文件验证成功",
            "table_count": len(tables),
            "tables": [table[0] for table in tables[:10]]  # 只返回前10个表名
        })
    except sqlite3.DatabaseError as e:
        # 删除临时文件
        if os.path.exists(filepath):
            os.remove(filepath)
        return JSONResponse(content={
            "success": False,
            "error": f"无效的SQLite文件: {str(e)}"
        }, status_code=400)
    except Exception as e:
        # 删除临时文件
        if os.path.exists(filepath):
            os.remove(filepath)
        return JSONResponse(content={
            "success": False,
            "error": f"验证过程中发生错误: {str(e)}"
        }, status_code=500)


@app.post("/migrate")
async def migrate_database(
    sqlite_file: UploadFile = File(...),
    pg_host: str = Form("localhost"),
    pg_port: str = Form("5432"),
    pg_database: str = Form("moviepilot"),
    pg_user: str = Form("moviepilot"),
    pg_password: str = Form("moviepilot")
):
    try:
        # 保存上传的文件
        filename = sqlite_file.filename
        filepath = os.path.join('uploads', filename)
        
        with open(filepath, 'wb') as f:
            content = await sqlite_file.read()
            f.write(content)
        
        # 获取PostgreSQL配置
        pg_config = {
            'host': pg_host,
            'port': pg_port,
            'database': pg_database,
            'user': pg_user,
            'password': pg_password
        }
        
        # 执行迁移
        result = perform_migration(filepath, pg_config)
        return JSONResponse(content={"success": True, "message": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/migrate-server")
async def migrate_server_database(
    server_file_path: str = Form(...),
    pg_host: str = Form("localhost"),
    pg_port: str = Form("5432"),
    pg_database: str = Form("moviepilot"),
    pg_user: str = Form("moviepilot"),
    pg_password: str = Form("moviepilot")
):
    try:
        # 检查服务器上的文件是否存在
        if not os.path.exists(server_file_path):
            return JSONResponse(content={"error": f"服务器上找不到文件: {server_file_path}"}, status_code=400)
        
        # 检查文件扩展名
        if not server_file_path.endswith(('.db', '.sqlite', '.sqlite3')):
            return JSONResponse(content={"error": "文件必须是SQLite数据库文件(.db, .sqlite, .sqlite3)"}, status_code=400)
        
        # 获取PostgreSQL配置
        pg_config = {
            'host': pg_host,
            'port': pg_port,
            'database': pg_database,
            'user': pg_user,
            'password': pg_password
        }
        
        # 执行迁移
        result = perform_migration(server_file_path, pg_config)
        return JSONResponse(content={"success": True, "message": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/backup")
async def backup_database(
    pg_host: str = Form("localhost"),
    pg_port: str = Form("5432"),
    pg_database: str = Form("moviepilot"),
    pg_user: str = Form("moviepilot"),
    pg_password: str = Form("moviepilot")
):
    try:
        # 获取PostgreSQL配置
        pg_config = {
            'host': pg_host,
            'port': pg_port,
            'database': pg_database,
            'user': pg_user,
            'password': pg_password
        }
        
        # 执行备份
        backup_file = perform_backup(pg_config)
        return FileResponse(backup_file, filename=os.path.basename(backup_file))
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/restore")
async def restore_database(
    backup_file: UploadFile = File(...),
    pg_host: str = Form("localhost"),
    pg_port: str = Form("5432"),
    pg_database: str = Form("moviepilot"),
    pg_user: str = Form("moviepilot"),
    pg_password: str = Form("moviepilot")
):
    try:
        # 保存上传的文件
        filename = backup_file.filename
        filepath = os.path.join('uploads', filename)
        
        with open(filepath, 'wb') as f:
            content = await backup_file.read()
            f.write(content)
        
        # 获取PostgreSQL配置
        pg_config = {
            'host': pg_host,
            'port': pg_port,
            'database': pg_database,
            'user': pg_user,
            'password': pg_password
        }
        
        # 执行恢复
        result = perform_restore(filepath, pg_config)
        return JSONResponse(content={"success": True, "message": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


def perform_migration(sqlite_file, pg_config):
    """执行SQLite到PostgreSQL的迁移"""
    try:
        # 检查SQLite文件是否存在
        if not os.path.exists(sqlite_file):
            return f"错误: SQLite文件不存在: {sqlite_file}"
        
        # 使用pgloader进行迁移
        pg_conn_string = f"postgresql://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
        sqlite_conn_string = f"sqlite://{sqlite_file}"
        
        # 构建pgloader命令
        command = [
            'pgloader',
            '--verbose',
            sqlite_conn_string,
            pg_conn_string
        ]
        
        # 执行命令
        result = subprocess.run(command, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            return f"迁移成功完成"
        else:
            return f"迁移失败: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "迁移超时，请稍后重试"
    except Exception as e:
        return f"迁移过程中发生错误: {str(e)}"


def perform_backup(pg_config):
    """执行PostgreSQL数据库备份"""
    try:
        # 确保导出目录存在
        os.makedirs('exports', exist_ok=True)
        
        # 使用pg_dump进行备份
        backup_filename = f"backup_{pg_config['database']}_{int(time.time())}.sql"
        backup_path = os.path.join('exports', backup_filename)
        
        command = [
            'pg_dump',
            '-h', pg_config['host'],
            '-p', pg_config['port'],
            '-U', pg_config['user'],
            '-d', pg_config['database'],
            '-f', backup_path
        ]
        
        # 设置环境变量用于密码
        env = os.environ.copy()
        env['PGPASSWORD'] = pg_config['password']
        
        # 执行命令
        result = subprocess.run(command, capture_output=True, text=True, timeout=600, env=env)
        
        if result.returncode == 0:
            return backup_path
        else:
            raise Exception(f"备份失败: {result.stderr}")
    except subprocess.TimeoutExpired:
        raise Exception("备份超时，请稍后重试")
    except Exception as e:
        raise Exception(f"备份过程中发生错误: {str(e)}")


def perform_restore(backup_file, pg_config):
    """执行PostgreSQL数据库恢复"""
    try:
        # 检查备份文件是否存在
        if not os.path.exists(backup_file):
            return f"错误: 备份文件不存在: {backup_file}"
        
        # 使用psql进行恢复
        command = [
            'psql',
            '-h', pg_config['host'],
            '-p', pg_config['port'],
            '-U', pg_config['user'],
            '-d', pg_config['database'],
            '-f', backup_file
        ]
        
        # 设置环境变量用于密码
        env = os.environ.copy()
        env['PGPASSWORD'] = pg_config['password']
        
        # 执行命令
        result = subprocess.run(command, capture_output=True, text=True, timeout=600, env=env)
        
        if result.returncode == 0:
            return f"恢复成功完成"
        else:
            return f"恢复失败: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "恢复超时，请稍后重试"
    except Exception as e:
        return f"恢复过程中发生错误: {str(e)}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5055)