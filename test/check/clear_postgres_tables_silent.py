#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空 PostgreSQL 中的表（无需确认）
"""

import psycopg2

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
    print("清空 PostgreSQL 表")
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
            print("\n数据库中没有表")
            conn.close()
            return True
        
        print(f"\n数据库中的表:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} 条记录")
        
        print("\n开始清空表...")
        
        # 清空表（按依赖顺序）
        tables_to_clear = ['grab_record', 'kline_data', 'base_data']
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"  ✅ 已清空 {table}")
            except Exception as e:
                print(f"  ❌ 清空 {table} 失败: {e}")
        
        conn.commit()
        
        # 验证清空结果
        print("\n" + "=" * 60)
        print("清空结果:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} 条记录")
        
        cursor.close()
        conn.close()
        
        print("\n✅ 表已清空!")
        return True
        
    except Exception as e:
        print(f"\n❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = clear_tables()
    exit(0 if success else 1)
