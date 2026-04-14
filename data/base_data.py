import akshare as ak
import duckdb
import os
import sys
import requests
import pandas as pd
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_converter import convert_code, get_exchange, is_a_stock, is_fund


DB_PATH = r'D:\dev\ai\ivydata\db\ivy.duckdb'


def get_all_stocks():
    """获取沪深京三地全部A股列表"""
    try:
        df = ak.stock_info_a_code_name()
        print(f"成功获取{len(df)}只股票列表")
        return df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return None


def get_all_funds():
    """获取天天基金网场内交易基金列表"""
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


def init_db():
    """初始化数据库和表"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = duckdb.connect(DB_PATH)

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS t_base (
        code VARCHAR,
        name VARCHAR,
        code_converted VARCHAR,
        exchange VARCHAR,
        stock_or_fund INTEGER,
        PRIMARY KEY (code)
    )
    """
    conn.execute(create_table_sql)
    print("数据库和表创建完成")
    return conn


def insert_stocks(conn):
    """插入股票数据"""
    stock_df = get_all_stocks()
    if stock_df is None:
        return 0

    stock_df = stock_df[['code', 'name']].copy()
    stock_df['code_converted'] = stock_df['code'].apply(convert_code)
    stock_df['exchange'] = stock_df['code'].apply(get_exchange)
    stock_df['stock_or_fund'] = 1

    conn.execute("DELETE FROM t_base WHERE stock_or_fund = 1")

    conn.register('stock_data', stock_df)
    conn.execute("""
        INSERT INTO t_base (code, name, code_converted, exchange, stock_or_fund)
        SELECT code, name, code_converted, exchange, stock_or_fund FROM stock_data
    """)
    conn.unregister('stock_data')

    count = len(stock_df)
    print(f"成功插入{count}条股票数据")
    return count


def insert_funds(conn):
    """插入基金数据"""
    fund_df = get_all_funds()
    if fund_df is None:
        return 0

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
        return 0

    fund_df['code'] = fund_df['code'].astype(str).str.zfill(6)
    fund_df['code_converted'] = fund_df['code'].apply(convert_code)
    fund_df['exchange'] = fund_df['code'].apply(get_exchange)
    fund_df['stock_or_fund'] = 2

    conn.execute("DELETE FROM t_base WHERE stock_or_fund = 2")

    conn.register('fund_data', fund_df)
    conn.execute("""
        INSERT INTO t_base (code, name, code_converted, exchange, stock_or_fund)
        SELECT code, name, code_converted, exchange, stock_or_fund FROM fund_data
    """)
    conn.unregister('fund_data')

    count = len(fund_df)
    print(f"成功插入{count}条基金数据")
    return count


def main():
    """主函数"""
    print("开始初始化基础数据...")

    conn = init_db()

    stock_count = insert_stocks(conn)
    fund_count = insert_funds(conn)

    result = conn.execute("SELECT COUNT(*) FROM t_base").fetchone()
    print(f"表中总数据量: {result[0]}")

    stock_result = conn.execute("SELECT COUNT(*) FROM t_base WHERE stock_or_fund = 1").fetchone()
    fund_result = conn.execute("SELECT COUNT(*) FROM t_base WHERE stock_or_fund = 2").fetchone()
    print(f"股票数量: {stock_result[0]}, 基金数量: {fund_result[0]}")

    sample = conn.execute("SELECT * FROM t_base LIMIT 5").fetchall()
    print("示例数据:")
    for row in sample:
        print(f"  {row}")

    conn.close()
    print("数据初始化完成!")


if __name__ == "__main__":
    main()
