#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 连接检查脚本
"""

import psycopg2
from psycopg2 import OperationalError

# PostgreSQL 配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'ivydata',
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF'
}

def check_postgres_connection():
    """检查 PostgreSQL 连接"""
    print("=" * 60)
    print("PostgreSQL 连接检查")
    print("=" * 60)
    
    print(f"\n配置信息:")
    print(f"  主机: {DB_CONFIG['host']}")
    print(f"  端口: {DB_CONFIG['port']}")
    print(f"  数据库: {DB_CONFIG['database']}")
    print(f"  用户: {DB_CONFIG['user']}")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"\n[OK] PostgreSQL 连接成功!")
        
        # 获取 PostgreSQL 版本
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"  版本: {version[0].split()[0]}")
        
        # 检查表是否存在
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"\n数据库中的表:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} 条记录")
        
        cursor.close()
        conn.close()
        
        print(f"\n[OK] 检查完成!")
        return True
        
    except OperationalError as e:
        print(f"\n[ERROR] PostgreSQL 连接失败!")
        print(f"  错误: {e}")
        print(f"\n请确保:")
        print(f"  1. PostgreSQL 服务已启动")
        print(f"  2. 数据库配置正确")
        print(f"  3. 用户权限正确")
        return False
    except Exception as e:
        print(f"\n[ERROR] 检查过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = check_postgres_connection()
    exit(0 if success else 1)
