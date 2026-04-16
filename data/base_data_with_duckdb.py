#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础数据抓取脚本（使用DuckDB临时存储，批量导入PostgreSQL）
"""

import os
import sys
import duckdb
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import akshare as ak
from datetime import datetime
import traceback

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 数据库配置
TEMP_DB_PATH = 'D:\\dev\\ai\\ivydata\\db\\temp_ivy.duckdb'

POSTGRESQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'ivydata',
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF'
}

def ensure_log_dir():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def log(message, end='\n'):
    print(message, end=end)
    ensure_log_dir()
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', f'base_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + end)


def print_error(message):
    log(f"\n{'='*50}")
    log(f"错误: {message}")
    log(f"{'='*50}\n")


def print_warning(message):
    log(f"\n警告: {message}\n")


def init_temp_db():
    """初始化临时DuckDB数据库"""
    try:
        if os.path.exists(TEMP_DB_PATH):
            log(f"删除旧的临时数据库...")
            os.remove(TEMP_DB_PATH)
        
        log(f"创建临时DuckDB数据库...")
        conn = duckdb.connect(TEMP_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE base_data (
                id INTEGER PRIMARY KEY,
                code VARCHAR(20),
                name VARCHAR(100),
                exchange VARCHAR(10),
                stock_or_fund INTEGER,
                code_converted VARCHAR(50),
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE grab_record (
                id INTEGER PRIMARY KEY,
                type VARCHAR(50),
                status VARCHAR(20),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                result TEXT
            )
        """)
        
        conn.commit()
        return conn
    except Exception as e:
        print_error(f"初始化临时数据库失败\n详细信息: {e}")
        raise SystemExit(1)


def fetch_stock_info():
    """获取A股列表"""
    try:
        log("正在获取A股列表...")
        
        stock_info_a_code_name_df = ak.stock_info_a_code_name()
        stock_list = stock_info_a_code_name_df.to_dict('records')
        
        log(f"成功获取 {len(stock_list)} 只A股信息")
        return stock_list
    except Exception as e:
        print_error(f"获取A股列表失败\n详细信息: {e}")
        return []


def fetch_fund_info():
    """获取场内基金列表"""
    try:
        log("正在获取场内基金列表...")
        
        fund_etf_spot_ths_df = ak.fund_etf_spot_ths(symbol="ETF基金")
        fund_list = []
        
        if fund_etf_spot_ths_df is not None and len(fund_etf_spot_ths_df) > 0:
            for _, row in fund_etf_spot_ths_df.iterrows():
                fund_list.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', ''))
                })
        
        log(f"成功获取 {len(fund_list)} 只场内基金信息")
        return fund_list
    except Exception as e:
        print_error(f"获取场内基金列表失败\n详细信息: {e}")
        return []


def convert_code(code, stock_or_fund):
    """转换股票代码格式"""
    if stock_or_fund == 1:
        if code.startswith('6'):
            return f"{code}.SH"
        else:
            return f"{code}.SZ"
    else:
        return f"{code}.SZ"


def save_to_duckdb(conn, stock_list, fund_list):
    """保存数据到临时DuckDB"""
    try:
        cursor = conn.cursor()
        now = datetime.now()
        
        all_data = []
        id_counter = 1
        
        for stock in stock_list:
            all_data.append({
                'id': id_counter,
                'code': stock['code'],
                'name': stock['name'],
                'exchange': 'SH' if stock['code'].startswith('6') else 'SZ',
                'stock_or_fund': 1,
                'code_converted': convert_code(stock['code'], 1),
                'created_at': now,
                'updated_at': now
            })
            id_counter += 1
        
        for fund in fund_list:
            all_data.append({
                'id': id_counter,
                'code': fund['code'],
                'name': fund['name'],
                'exchange': 'SZ',
                'stock_or_fund': 2,
                'code_converted': convert_code(fund['code'], 2),
                'created_at': now,
                'updated_at': now
            })
            id_counter += 1
        
        log(f"正在将 {len(all_data)} 条数据写入临时DuckDB...")
        
        for item in all_data:
            cursor.execute("""
                INSERT INTO base_data (id, code, name, exchange, stock_or_fund, code_converted, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['id'],
                item['code'],
                item['name'],
                item['exchange'],
                item['stock_or_fund'],
                item['code_converted'],
                item['created_at'],
                item['updated_at']
            ))
        
        cursor.execute("""
            INSERT INTO grab_record (id, type, status, start_time, end_time, result)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            1,
            'base_data',
            'completed',
            now,
            now,
            f'Successfully fetched {len(stock_list)} stocks and {len(fund_list)} funds'
        ))
        
        conn.commit()
        log(f"成功写入临时DuckDB: {len(all_data)} 条基础数据")
        return len(all_data)
    except Exception as e:
        print_error(f"保存到临时DuckDB失败\n详细信息: {e}")
        raise SystemExit(1)


def transfer_to_postgresql(duckdb_conn):
    """从DuckDB迁移数据到PostgreSQL"""
    try:
        log(f"\n开始从临时DuckDB迁移数据到PostgreSQL...")
        
        pg_conn = psycopg2.connect(**POSTGRESQL_CONFIG)
        pg_cursor = pg_conn.cursor()
        
        duckdb_cursor = duckdb_conn.cursor()
        
        # 读取DuckDB中的数据
        duckdb_cursor.execute("SELECT * FROM base_data ORDER BY id")
        base_data_rows = duckdb_cursor.fetchall()
        
        log(f"从DuckDB读取到 {len(base_data_rows)} 条基础数据")
        
        # 清空PostgreSQL表
        pg_cursor.execute("TRUNCATE TABLE base_data RESTART IDENTITY CASCADE")
        pg_cursor.execute("TRUNCATE TABLE grab_record RESTART IDENTITY CASCADE")
        log(f"已清空PostgreSQL中的旧数据")
        
        # 批量插入到PostgreSQL
        insert_data = []
        for row in base_data_rows:
            insert_data.append((
                row[1],  # code
                row[2],  # name
                row[3],  # exchange
                row[4],  # stock_or_fund
                row[5],  # code_converted
                row[6],  # created_at
                row[7]   # updated_at
            ))
        
        execute_values(pg_cursor, """
            INSERT INTO base_data (code, name, exchange, stock_or_fund, code_converted, created_at, updated_at)
            VALUES %s
        """, insert_data)
        
        # 插入抓取记录
        duckdb_cursor.execute("SELECT * FROM grab_record")
        grab_record = duckdb_cursor.fetchone()
        
        if grab_record:
            pg_cursor.execute("""
                INSERT INTO grab_record (type, status, start_time, end_time, result)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                grab_record[1],
                grab_record[2],
                grab_record[3],
                grab_record[4],
                grab_record[5]
            ))
        
        pg_conn.commit()
        pg_cursor.close()
        pg_conn.close()
        
        log(f"成功迁移 {len(insert_data)} 条数据到PostgreSQL")
        return True
    except Exception as e:
        print_error(f"迁移到PostgreSQL失败\n详细信息: {e}")
        raise SystemExit(1)


def delete_temp_db():
    """删除临时DuckDB"""
    try:
        if os.path.exists(TEMP_DB_PATH):
            log(f"删除临时DuckDB文件...")
            os.remove(TEMP_DB_PATH)
            
            wal_file = TEMP_DB_PATH + '.wal'
            if os.path.exists(wal_file):
                os.remove(wal_file)
            
            log(f"临时数据库已删除")
    except Exception as e:
        print_warning(f"删除临时数据库失败: {e}")


def graceful_exit(conn, message):
    print_error(message)
    if conn:
        try:
            conn.close()
        except:
            pass
    delete_temp_db()
    raise SystemExit(1)


def main():
    log("=" * 50)
    log("基础数据抓取程序启动（DuckDB临时存储版）")
    log("=" * 50)

    duckdb_conn = None

    try:
        # 1. 初始化临时DuckDB
        duckdb_conn = init_temp_db()

        # 2. 获取数据
        stock_list = fetch_stock_info()
        fund_list = fetch_fund_info()

        if not stock_list and not fund_list:
            graceful_exit(duckdb_conn, "没有获取到任何数据")

        log(f"\n总计获取 {len(stock_list)} 只股票，{len(fund_list)} 只基金")

        # 3. 保存到DuckDB
        save_to_duckdb(duckdb_conn, stock_list, fund_list)

        # 4. 迁移到PostgreSQL
        transfer_to_postgresql(duckdb_conn)

        # 5. 关闭DuckDB连接
        duckdb_conn.close()
        duckdb_conn = None

        # 6. 删除临时DuckDB
        delete_temp_db()

        log("\n" + "=" * 50)
        log("数据抓取和导入完成!")
        log("=" * 50)

        import json
        print("\n___JSON_OUTPUT_START___")
        print(json.dumps({
            "stocks": len(stock_list), 
            "funds": len(fund_list), 
            "total": len(stock_list) + len(fund_list)
        }))
        print("___JSON_OUTPUT_END___")

    except SystemExit:
        raise
    except KeyboardInterrupt:
        graceful_exit(duckdb_conn, "用户中断程序")
    except Exception as e:
        error_details = traceback.format_exc()
        print_error(f"程序执行过程中发生未预期的错误\n{error_details}")
        log(f"\n已处理成功的数据已保存到临时数据库")
        log(f"未处理成功的代码可在下次运行时重新处理")
        if duckdb_conn:
            try:
                duckdb_conn.close()
            except:
                pass
        raise SystemExit(1)
    else:
        if duckdb_conn:
            try:
                duckdb_conn.close()
            except:
                pass


if __name__ == "__main__":
    main()
