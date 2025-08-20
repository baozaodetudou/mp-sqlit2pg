#!/usr/bin/env python3
"""
测试SQLite到PostgreSQL迁移工具
"""

import requests
import os
import time

# 测试配置
BASE_URL = "http://localhost:5055"
TEST_DB_CONFIG = {
    "pg_host": "localhost",
    "pg_port": "5432",
    "pg_database": "moviepilot",
    "pg_user": "moviepilot",
    "pg_password": "moviepilot"
}

def test_server_running():
    """测试服务器是否运行"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✓ 服务器运行正常")
            return True
        else:
            print("✗ 服务器返回错误状态码:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务器，请确保服务器正在运行")
        return False

def test_migration_endpoint():
    """测试迁移端点"""
    print("\n测试迁移端点...")
    try:
        # 创建一个简单的测试SQLite数据库
        import sqlite3
        test_db_path = "test.db"
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # 创建测试表并插入数据
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value INTEGER
            )
        """)
        
        cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test1", 100))
        cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", ("test2", 200))
        conn.commit()
        conn.close()
        
        # 准备文件上传
        with open(test_db_path, 'rb') as f:
            files = {'sqlite_file': f}
            data = TEST_DB_CONFIG.copy()
            
            response = requests.post(f"{BASE_URL}/migrate", files=files, data=data)
            
        # 清理测试文件
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✓ 迁移端点测试通过")
                return True
            else:
                print("✗ 迁移失败:", result.get("message", "未知错误"))
                return False
        else:
            print("✗ 迁移端点返回错误状态码:", response.status_code)
            print("响应内容:", response.text)
            return False
    except Exception as e:
        print("✗ 迁移端点测试失败:", str(e))
        return False

def test_backup_endpoint():
    """测试备份端点"""
    print("\n测试备份端点...")
    try:
        response = requests.post(f"{BASE_URL}/backup", data=TEST_DB_CONFIG)
        
        if response.status_code == 200:
            # 保存备份文件
            with open("test_backup.sql", "wb") as f:
                f.write(response.content)
            print("✓ 备份端点测试通过，备份文件已保存为 test_backup.sql")
            
            # 清理备份文件
            if os.path.exists("test_backup.sql"):
                os.remove("test_backup.sql")
            return True
        else:
            print("✗ 备份端点返回错误状态码:", response.status_code)
            print("响应内容:", response.text)
            return False
    except Exception as e:
        print("✗ 备份端点测试失败:", str(e))
        return False

def test_restore_endpoint():
    """测试恢复端点"""
    print("\n测试恢复端点...")
    try:
        # 创建一个简单的SQL备份文件
        backup_content = """
-- 测试备份文件
CREATE TABLE IF NOT EXISTS restore_test (
    id SERIAL PRIMARY KEY,
    test_data VARCHAR(50)
);

INSERT INTO restore_test (test_data) VALUES ('test value');
"""
        backup_file_path = "test_restore.sql"
        with open(backup_file_path, 'w') as f:
            f.write(backup_content)
        
        # 准备文件上传
        with open(backup_file_path, 'rb') as f:
            files = {'backup_file': f}
            data = TEST_DB_CONFIG.copy()
            
            response = requests.post(f"{BASE_URL}/restore", files=files, data=data)
            
        # 清理测试文件
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)
            
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✓ 恢复端点测试通过")
                return True
            else:
                print("✗ 恢复失败:", result.get("message", "未知错误"))
                return False
        else:
            print("✗ 恢复端点返回错误状态码:", response.status_code)
            print("响应内容:", response.text)
            return False
    except Exception as e:
        print("✗ 恢复端点测试失败:", str(e))
        return False

def main():
    """主测试函数"""
    print("开始测试SQLite到PostgreSQL迁移工具...")
    print("=" * 50)
    
    # 测试服务器是否运行
    if not test_server_running():
        print("\n请先启动服务器:")
        print("cd /path/to/your/project")
        print("python app.py")
        return
    
    # 测试各个端点
    tests = [
        test_migration_endpoint,
        test_backup_endpoint,
        test_restore_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # 避免请求过快
    
    print("\n" + "=" * 50)
    print(f"测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败，请检查上述错误信息")

if __name__ == "__main__":
    main()