import akshare as ak
import duckdb
import os
import pandas as pd
import code_converter as cc

def get_all_stocks():
    """获取沪深京三地全部A股列表"""
    try:
        df = ak.stock_info_a_code_name()
        print(f"成功获取{len(df)}只股票列表")
        return df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return None

db_path = r'D:\dev\ai\ivydata\db\fund.duckdb'
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = duckdb.connect(db_path)

create_table_sql = """
CREATE TABLE IF NOT EXISTS stock_list (
    code VARCHAR,
    name VARCHAR,
    code_converted VARCHAR,
    exchange VARCHAR,
    is_stock BOOLEAN,
    is_fund BOOLEAN,
    PRIMARY KEY (code)
)
"""
conn.execute(create_table_sql)

conn.execute("ALTER TABLE stock_list ADD COLUMN IF NOT EXISTS code_converted VARCHAR")
conn.execute("ALTER TABLE stock_list ADD COLUMN IF NOT EXISTS exchange VARCHAR")
conn.execute("ALTER TABLE stock_list ADD COLUMN IF NOT EXISTS is_stock BOOLEAN")
conn.execute("ALTER TABLE stock_list ADD COLUMN IF NOT EXISTS is_fund BOOLEAN")

stock_list = get_all_stocks()
if stock_list is not None:
    print(stock_list.head())
    
    stock_list['code_converted'] = stock_list['code'].apply(cc.convert_code)
    stock_list['exchange'] = stock_list['code'].apply(cc.get_exchange)
    stock_list['is_stock'] = stock_list['code'].apply(cc.is_a_stock)
    stock_list['is_fund'] = stock_list['code'].apply(cc.is_fund)
    
    print(stock_list.head())
    
    conn.execute("DELETE FROM stock_list")
    
    conn.register('stock_df', stock_list)
    conn.execute("""
        INSERT INTO stock_list (code, name, code_converted, exchange, is_stock, is_fund)
        SELECT code, name, code_converted, exchange, is_stock, is_fund FROM stock_df
    """)
    conn.unregister('stock_df')
    
    result = conn.execute("SELECT COUNT(*) FROM stock_list").fetchone()
    print(f"表中股票数量: {result[0]}")

conn.close()
