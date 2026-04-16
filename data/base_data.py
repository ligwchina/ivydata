import akshare as ak
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
import requests
import pandas as pd
from io import StringIO

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_converter import convert_code, get_exchange, is_a_stock, is_fund

# PostgreSQL 配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'ivydata',
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查并创建 base_data 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS base_data (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            code_converted VARCHAR(20) NOT NULL,
            exchange VARCHAR(10) NOT NULL,
            stock_or_fund INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    return conn

def get_all_stocks():
    try:
        df = ak.stock_info_a_code_name()
        print(f"成功获取{len(df)}只股票列表")
        return df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return None

def get_all_funds():
    try:
        from akshare.utils.cons import headers
        url = "https://fund.eastmoney.com/cnjy_jzzzl.html"
        r = requests.get(url, headers=headers, timeout=30)
        r.encoding = "gb2312"
        temp_df = pd.read_html(StringIO(r.text))[1]
        temp_df = temp_df.iloc[2:].copy()
        temp_df = temp_df[[3, 4, 5]].reset_index(drop=True)
        temp_df.columns = ["基金代码", "基金简称", "类型"]
        temp_df["基金简称"] = temp_df["基金简称"].str.replace("行情吧档案", "")
        print(f"成功获取{len(temp_df)}只基金列表")
        return temp_df
    except Exception as e:
        print(f"获取基金列表失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def insert_stocks(conn, incremental=True):
    stock_df = get_all_stocks()
    if stock_df is None:
        return 0, 0

    stock_df = stock_df[['code', 'name']].copy()
    stock_df['code_converted'] = stock_df['code'].apply(convert_code)
    stock_df['exchange'] = stock_df['code'].apply(get_exchange)
    stock_df['stock_or_fund'] = 1

    cursor = conn.cursor()
    
    if incremental:
        cursor.execute("SELECT code FROM base_data WHERE stock_or_fund = 1")
        existing_codes = {row[0] for row in cursor.fetchall()}
    else:
        cursor.execute("DELETE FROM base_data WHERE stock_or_fund = 1")
        existing_codes = set()

    new_df = stock_df[~stock_df['code'].isin(existing_codes)]
    update_df = stock_df[stock_df['code'].isin(existing_codes)]

    added_count = 0
    updated_count = 0

    # 批量插入新数据
    if len(new_df) > 0:
        insert_data = []
        for _, row in new_df.iterrows():
            insert_data.append((
                row['code'],
                row['name'],
                row['code_converted'],
                row['exchange'],
                row['stock_or_fund']
            ))
        
        execute_values(cursor, """
            INSERT INTO base_data (code, name, code_converted, exchange, stock_or_fund)
            VALUES %s
        """, insert_data)
        added_count = len(new_df)

    # 更新现有数据
    if len(update_df) > 0:
        for _, row in update_df.iterrows():
            cursor.execute("""
                UPDATE base_data 
                SET name = %s, code_converted = %s, exchange = %s, updated_at = CURRENT_TIMESTAMP
                WHERE code = %s AND stock_or_fund = 1
            """, (row['name'], row['code_converted'], row['exchange'], row['code']))
            updated_count += 1

    conn.commit()
    print(f"股票数据 - 新增: {added_count}条, 更新: {updated_count}条")
    return added_count, updated_count

def insert_funds(conn, incremental=True):
    fund_df = get_all_funds()
    if fund_df is None:
        return 0, 0

    if '基金代码' in fund_df.columns and '基金简称' in fund_df.columns:
        fund_df = fund_df[['基金代码', '基金简称']].copy()
        fund_df.columns = ['code', 'name']
    elif '代码' in fund_df.columns and '名称' in fund_df.columns:
        fund_df = fund_df[['代码', '名称']].copy()
        fund_df.columns = ['code', 'name']
    elif 'code' in fund_df.columns and 'name' in fund_df.columns:
        fund_df = fund_df[['code', 'name']].copy()
    else:
        print(f"基金数据列名: {fund_df.columns.tolist()}")
        return 0, 0

    fund_df['code'] = fund_df['code'].astype(str).str.zfill(6)
    fund_df['code_converted'] = fund_df['code'].apply(convert_code)
    fund_df['exchange'] = fund_df['code'].apply(get_exchange)
    fund_df['stock_or_fund'] = 2

    cursor = conn.cursor()
    
    if incremental:
        cursor.execute("SELECT code FROM base_data WHERE stock_or_fund = 2")
        existing_codes = {row[0] for row in cursor.fetchall()}
    else:
        cursor.execute("DELETE FROM base_data WHERE stock_or_fund = 2")
        existing_codes = set()

    new_df = fund_df[~fund_df['code'].isin(existing_codes)]
    update_df = fund_df[fund_df['code'].isin(existing_codes)]

    added_count = 0
    updated_count = 0

    # 批量插入新数据
    if len(new_df) > 0:
        insert_data = []
        for _, row in new_df.iterrows():
            insert_data.append((
                row['code'],
                row['name'],
                row['code_converted'],
                row['exchange'],
                row['stock_or_fund']
            ))
        
        execute_values(cursor, """
            INSERT INTO base_data (code, name, code_converted, exchange, stock_or_fund)
            VALUES %s
        """, insert_data)
        added_count = len(new_df)

    # 更新现有数据
    if len(update_df) > 0:
        for _, row in update_df.iterrows():
            cursor.execute("""
                UPDATE base_data 
                SET name = %s, code_converted = %s, exchange = %s, updated_at = CURRENT_TIMESTAMP
                WHERE code = %s AND stock_or_fund = 2
            """, (row['name'], row['code_converted'], row['exchange'], row['code']))
            updated_count += 1

    conn.commit()
    print(f"基金数据 - 新增: {added_count}条, 更新: {updated_count}条")
    return added_count, updated_count

def main(incremental=True):
    if incremental:
        print("开始增量更新基础数据...")
    else:
        print("开始全量初始化基础数据...")

    conn = init_db()

    stock_added, stock_updated = insert_stocks(conn, incremental)
    fund_added, fund_updated = insert_funds(conn, incremental)

    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM base_data")
    result = cursor.fetchone()
    print(f"\n表中总数据量: {result[0]}")

    cursor.execute("SELECT COUNT(*) FROM base_data WHERE stock_or_fund = 1")
    stock_result = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) FROM base_data WHERE stock_or_fund = 2")
    fund_result = cursor.fetchone()
    
    print(f"股票数量: {stock_result[0]}, 基金数量: {fund_result[0]}")

    print(f"\n更新统计:")
    print(f"  股票 - 新增: {stock_added}, 更新: {stock_updated}")
    print(f"  基金 - 新增: {fund_added}, 更新: {fund_updated}")

    cursor.execute("SELECT code, name, code_converted, exchange, stock_or_fund FROM base_data ORDER BY stock_or_fund, code LIMIT 5")
    sample = cursor.fetchall()
    print("\n示例数据:")
    for row in sample:
        print(f"  {row}")

    import json
    cursor.execute("SELECT code, name, code_converted, exchange, stock_or_fund FROM base_data ORDER BY stock_or_fund, code")
    all_data = cursor.fetchall()
    result = []
    for row in all_data:
        result.append({
            'code': row[0],
            'name': row[1],
            'code_converted': row[2],
            'exchange': row[3],
            'stock_or_fund': row[4]
        })
    print("\n___JSON_OUTPUT_START___")
    print(json.dumps(result, ensure_ascii=False))
    print("___JSON_OUTPUT_END___")

    conn.close()
    print("\n数据更新完成!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='初始化或更新基础数据')
    parser.add_argument('--full', action='store_true', help='全量替换模式（默认是增量模式）')
    args = parser.parse_args()
    
    main(incremental=not args.full)
