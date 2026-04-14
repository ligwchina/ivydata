import duckdb
import os
import pandas as pd
import code_converter as cc

db_path = r'D:\dev\ai\ivydata\db\fund.duckdb'
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = duckdb.connect(db_path)

conn.execute("ALTER TABLE fund_etf ADD COLUMN IF NOT EXISTS code_converted VARCHAR")
conn.execute("ALTER TABLE fund_etf ADD COLUMN IF NOT EXISTS exchange VARCHAR")
conn.execute("ALTER TABLE fund_etf ADD COLUMN IF NOT EXISTS is_stock BOOLEAN")
conn.execute("ALTER TABLE fund_etf ADD COLUMN IF NOT EXISTS is_fund BOOLEAN")

etf_list = conn.execute("SELECT * FROM fund_etf").fetchdf()
if len(etf_list) > 0:
    print(f"获取到 {len(etf_list)} 条ETF记录")
    print(etf_list.head())
    
    etf_list['code_converted'] = etf_list['基金代码'].apply(cc.convert_code)
    etf_list['exchange'] = etf_list['基金代码'].apply(cc.get_exchange)
    etf_list['is_stock'] = etf_list['基金代码'].apply(cc.is_a_stock)
    etf_list['is_fund'] = etf_list['基金代码'].apply(cc.is_fund)
    
    print(etf_list.head())
    
    conn.execute("DELETE FROM fund_etf")
    
    conn.register('etf_df', etf_list)
    conn.execute("""
        INSERT INTO fund_etf (基金代码, 基金简称, 类型, code_converted, exchange, is_stock, is_fund)
        SELECT 基金代码, 基金简称, 类型, code_converted, exchange, is_stock, is_fund FROM etf_df
    """)
    conn.unregister('etf_df')
    
    result = conn.execute("SELECT COUNT(*) FROM fund_etf").fetchone()
    print(f"表中ETF数量: {result[0]}")

conn.close()
