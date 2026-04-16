#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

POSTGRESQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'ivydata',
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF'
}


def get_db_connection():
    return psycopg2.connect(**POSTGRESQL_CONFIG)


def ensure_table_exists(table_name, create_sql):
    """检查表是否存在，不存在则创建"""
    pg_conn = get_db_connection()
    pg_cursor = pg_conn.cursor()
    
    pg_cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = '{table_name}'
        )
    """)
    exists = pg_cursor.fetchone()[0]
    
    if not exists:
        pg_cursor.execute(create_sql)
    
    pg_conn.commit()
    pg_cursor.close()
    pg_conn.close()
    
    return exists


def ensure_all_tables():
    """确保所有需要的表都存在"""
    # base_data 表
    base_data_sql = """
        CREATE TABLE base_data (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            code_converted VARCHAR(20) NOT NULL,
            exchange VARCHAR(10) NOT NULL,
            stock_or_fund INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    ensure_table_exists('base_data', base_data_sql)
    
    # kline_data 表
    kline_data_sql = """
        CREATE TABLE kline_data (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            open NUMERIC(10, 2),
            high NUMERIC(10, 2),
            low NUMERIC(10, 2),
            close NUMERIC(10, 2),
            volume BIGINT,
            amount NUMERIC(20, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code, date)
        )
    """
    ensure_table_exists('kline_data', kline_data_sql)
    
    # grab_record 表
    grab_record_sql = """
        CREATE TABLE grab_record (
            id SERIAL PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL,
            message TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    ensure_table_exists('grab_record', grab_record_sql)
    
    # sys_options 表
    sys_options_sql = """
        CREATE TABLE sys_options (
            id SERIAL PRIMARY KEY,
            option_key VARCHAR(100) NOT NULL UNIQUE,
            option_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    existed = ensure_table_exists('sys_options', sys_options_sql)
    
    # 如果是新创建的表，初始化默认数据
    if not existed:
        pg_conn = get_db_connection()
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute("""
            INSERT INTO sys_options (option_key, option_value)
            VALUES 
                ('last_base_data_fetch', NULL),
                ('last_kline_data_fetch', NULL)
        """)
        pg_conn.commit()
        pg_cursor.close()
        pg_conn.close()


def update_sys_option(option_key, log_func=None):
    """更新 sys_options 表中的时间"""
    try:
        pg_conn = get_db_connection()
        pg_cursor = pg_conn.cursor()
        
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        pg_cursor.execute("""
            UPDATE sys_options 
            SET option_value = %s, updated_at = CURRENT_TIMESTAMP
            WHERE option_key = %s
        """, (now_str, option_key))
        
        pg_conn.commit()
        pg_cursor.close()
        pg_conn.close()
        
        if log_func:
            log_func(f"更新 sys_options.{option_key} 为: {now_str}")
    except Exception as e:
        if log_func:
            log_func(f"更新 sys_options 失败\n详细信息: {e}")
        else:
            print(f"更新 sys_options 失败\n详细信息: {e}")


def get_sys_option(option_key):
    """获取 sys_options 表中的值"""
    try:
        pg_conn = get_db_connection()
        pg_cursor = pg_conn.cursor()
        
        pg_cursor.execute("""
            SELECT option_value FROM sys_options WHERE option_key = %s
        """, (option_key,))
        result = pg_cursor.fetchone()
        
        pg_cursor.close()
        pg_conn.close()
        
        return result[0] if result else None
    except Exception as e:
        print(f"获取 sys_options 失败\n详细信息: {e}")
        return None
