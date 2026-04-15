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

conn = get_db_connection()

cur = conn.cursor()

cur.execute("""
    ALTER TABLE fund_etf ADD COLUMN IF NOT EXISTS code_converted VARCHAR(20)
""")
cur.execute("""
    ALTER TABLE fund_etf ADD COLUMN IF NOT EXISTS exchange VARCHAR(10)
""")
cur.execute("""
    ALTER TABLE fund_etf ADD COLUMN IF NOT EXISTS is_stock BOOLEAN
""")
cur.execute("""
    ALTER TABLE fund_etf ADD COLUMN IF NOT EXISTS is_fund BOOLEAN
""")

cur.execute("SELECT 基金代码, 基金简称, 类型 FROM fund_etf")
rows = cur.fetchall()

if len(rows) > 0:
    etf_list = pd.DataFrame(rows, columns=['基金代码', '基金简称', '类型'])
    print(f"获取到 {len(etf_list)} 条ETF记录")
    print(etf_list.head())
    
    etf_list['code_converted'] = etf_list['基金代码'].apply(cc.convert_code)
    etf_list['exchange'] = etf_list['基金代码'].apply(cc.get_exchange)
    etf_list['is_stock'] = etf_list['基金代码'].apply(cc.is_a_stock)
    etf_list['is_fund'] = etf_list['基金代码'].apply(cc.is_fund)
    
    print(etf_list.head())
    
    for _, row in etf_list.iterrows():
        cur.execute("""
            UPDATE fund_etf 
            SET code_converted = %s, exchange = %s, is_stock = %s, is_fund = %s
            WHERE 基金代码 = %s
        """, (row['code_converted'], row['exchange'], row['is_stock'], row['is_fund'], row['基金代码']))
    
    conn.commit()
    
    cur.execute("SELECT COUNT(*) FROM fund_etf")
    result = cur.fetchone()
    print(f"表中ETF数量: {result[0]}")

cur.close()
conn.close()
