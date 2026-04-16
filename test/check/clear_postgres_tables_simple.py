#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空 PostgreSQL 中的表（简单版本）
"""

import psycopg2
import sys

# PostgreSQL 配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'ivydata',
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF'
}

def clear_tables():
    """清空所有表"""
    print("=" * 60)
    print("Clear PostgreSQL Tables")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        if not tables:
            print("\nNo tables in database")
            conn.close()
            return True
        
        print("\nTables in database:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} records")
        
        print("\nClearing tables...")
        
        # 清空表（按依赖顺序）
        tables_to_clear = ['grab_record', 'kline_data', 'base_data']
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  [OK] Cleared {table}")
            except Exception as e:
                print(f"  [FAIL] Failed to clear {table}: {e}")
        
        conn.commit()
        
        # 验证清空结果
        print("\n" + "=" * 60)
        print("Result after clearing:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} records")
        
        cursor.close()
        conn.close()
        
        print("\n[SUCCESS] Tables cleared!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = clear_tables()
    sys.exit(0 if success else 1)
