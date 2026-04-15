import akshare as ak
import psycopg2
import os
import pandas as pd
import code_converter as cc

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF',
    'database': 'ivydata'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_all_stocks():
    """获取沪深京三地全部A股列表"""
    try:
        df = ak.stock_info_a_code_name()
        print(f"成功获取{len(df)}只股票列表")
        return df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return None

conn = get_db_connection()
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_list (
        id SERIAL PRIMARY KEY,
        code VARCHAR(20) NOT NULL UNIQUE,
        name VARCHAR(100) NOT NULL,
        code_converted VARCHAR(20) NOT NULL,
        exchange VARCHAR(10) NOT NULL,
        is_stock BOOLEAN NOT NULL,
        is_fund BOOLEAN NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

stock_list = get_all_stocks()
if stock_list is not None:
    print(stock_list.head())
    
    stock_list['code_converted'] = stock_list['code'].apply(cc.convert_code)
    stock_list['exchange'] = stock_list['code'].apply(cc.get_exchange)
    stock_list['is_stock'] = stock_list['code'].apply(cc.is_a_stock)
    stock_list['is_fund'] = stock_list['code'].apply(cc.is_fund)
    
    print(stock_list.head())
    
    cur.execute("DELETE FROM stock_list")
    
    for _, row in stock_list.iterrows():
        cur.execute("""
            INSERT INTO stock_list (code, name, code_converted, exchange, is_stock, is_fund)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                code_converted = EXCLUDED.code_converted,
                exchange = EXCLUDED.exchange,
                is_stock = EXCLUDED.is_stock,
                is_fund = EXCLUDED.is_fund,
                updated_at = CURRENT_TIMESTAMP
        """, (row['code'], row['name'], row['code_converted'], row['exchange'], row['is_stock'], row['is_fund']))
    
    conn.commit()
    
    cur.execute("SELECT COUNT(*) FROM stock_list")
    result = cur.fetchone()
    print(f"表中股票数量: {result[0]}")

cur.close()
conn.close()
