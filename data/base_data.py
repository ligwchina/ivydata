#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础数据抓取脚本（直接写入PostgreSQL）
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import akshare as ak
import requests
from io import StringIO
from datetime import datetime
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helper import ensure_all_tables, update_sys_option

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

POSTGRESQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'ivydata',
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF'
}


def get_db_connection():
    return psycopg2.connect(**POSTGRESQL_CONFIG)


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


def get_all_funds():
    try:
        log("正在获取基金列表...")
        from akshare.utils.cons import headers
        url = "https://fund.eastmoney.com/cnjy_jzzzl.html"
        r = requests.get(url, headers=headers, timeout=30)
        r.encoding = "gb2312"
        temp_df = pd.read_html(StringIO(r.text))[1]
        temp_df = temp_df.iloc[2:].copy()
        temp_df = temp_df[[3, 4, 5]].reset_index(drop=True)
        temp_df.columns = ["基金代码", "基金简称", "类型"]
        temp_df["基金简称"] = temp_df["基金简称"].str.replace("行情吧档案", "")
        log(f"成功获取{len(temp_df)}只基金列表")
        return temp_df
    except Exception as e:
        log(f"获取基金列表失败: {e}")
        traceback.print_exc()
        return None


def fetch_fund_info():
    """获取基金列表"""
    fund_df = get_all_funds()
    if fund_df is None:
        return []
    
    fund_list = []
    fund_codes = set()
    for _, row in fund_df.iterrows():
        code = str(row.get('基金代码', '')).zfill(6)
        name = str(row.get('基金简称', ''))
        if code and code not in fund_codes:
            fund_list.append({'code': code, 'name': name})
            fund_codes.add(code)
    
    log(f"总计获取 {len(fund_list)} 只基金信息")
    return fund_list


def convert_code(code, stock_or_fund):
    """转换股票代码格式"""
    if stock_or_fund == 1:
        if code.startswith('6'):
            return f"{code}.SH"
        else:
            return f"{code}.SZ"
    else:
        return f"{code}.SZ"


def insert_to_postgresql(stock_list, fund_list):
    """直接插入数据到PostgreSQL"""
    try:
        log(f"\n开始直接写入PostgreSQL...")
        
        pg_conn = get_db_connection()
        pg_cursor = pg_conn.cursor()
        
        now = datetime.now()
        
        all_data = []
        
        for stock in stock_list:
            all_data.append((
                stock['code'],
                stock['name'],
                'SH' if stock['code'].startswith('6') else 'SZ',
                1,
                convert_code(stock['code'], 1),
                now,
                now
            ))
        
        for fund in fund_list:
            all_data.append((
                fund['code'],
                fund['name'],
                'SZ',
                2,
                convert_code(fund['code'], 2),
                now,
                now
            ))
        
        log(f"正在将 {len(all_data)} 条数据写入PostgreSQL...")
        
        execute_values(pg_cursor, """
            INSERT INTO base_data (code, name, exchange, stock_or_fund, code_converted, created_at, updated_at)
            VALUES %s
            ON CONFLICT (code) DO NOTHING
        """, all_data)
        
        pg_cursor.execute("""
            INSERT INTO grab_record (type, status, start_time, end_time, message)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            'base_data',
            'completed',
            now,
            now,
            f'Successfully fetched {len(stock_list)} stocks and {len(fund_list)} funds'
        ))
        
        pg_conn.commit()
        pg_cursor.close()
        pg_conn.close()
        
        log(f"成功写入PostgreSQL: {len(all_data)} 条基础数据")
        
        update_sys_option('last_base_data_fetch', log_func=log)
        
        return len(all_data)
    except Exception as e:
        print_error(f"写入PostgreSQL失败\n详细信息: {e}")
        raise SystemExit(1)


def main():
    log("=" * 50)
    log("基础数据抓取程序启动（直接写入PostgreSQL版）")
    log("=" * 50)

    try:
        log("检查数据库表结构...")
        ensure_all_tables()

        stock_list = fetch_stock_info()
        fund_list = fetch_fund_info()

        if not stock_list and not fund_list:
            print_error("没有获取到任何数据")
            raise SystemExit(1)

        log(f"\n总计获取 {len(stock_list)} 只股票，{len(fund_list)} 只基金")

        insert_to_postgresql(stock_list, fund_list)

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
        print_error("用户中断程序")
        raise SystemExit(1)
    except Exception as e:
        error_details = traceback.format_exc()
        print_error(f"程序执行过程中发生未预期的错误\n{error_details}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
