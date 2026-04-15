import akshare as ak
import duckdb
import os
import sys
import requests
import pandas as pd
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_converter import convert_code, get_exchange, is_a_stock, is_fund
from config import DB_PATH


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
    conn = duckdb.connect(DB_PATH)

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS t_base (
        code VARCHAR PRIMARY KEY,
        name VARCHAR,
        code_converted VARCHAR,
        exchange VARCHAR,
        stock_or_fund INTEGER
    )
    """
    conn.execute(create_table_sql)
    conn.commit()
    print("数据库和表创建完成")
    return conn


def insert_stocks(conn, incremental=True):
    """插入股票数据
    incremental: True表示增量模式，只添加新数据并更新已有数据；False表示全量替换
    """
    stock_df = get_all_stocks()
    if stock_df is None:
        return 0, 0

    stock_df = stock_df[['code', 'name']].copy()
    stock_df['code_converted'] = stock_df['code'].apply(convert_code)
    stock_df['exchange'] = stock_df['code'].apply(get_exchange)
    stock_df['stock_or_fund'] = 1

    # 获取数据库中已有的股票代码
    existing_codes = set()
    result = conn.execute("SELECT code FROM t_base WHERE stock_or_fund = 1").fetchall()
    for row in result:
        existing_codes.add(row[0])

    # 分离新增和更新的数据
    new_df = stock_df[~stock_df['code'].isin(existing_codes)]
    update_df = stock_df[stock_df['code'].isin(existing_codes)]

    added_count = 0
    updated_count = 0

    if incremental:
        # 增量模式：添加新数据，更新已有数据
        if len(new_df) > 0:
            # 使用DuckDB的insert语句
            for _, row in new_df.iterrows():
                conn.execute('''
                    INSERT INTO t_base (code, name, code_converted, exchange, stock_or_fund)
                    VALUES (?, ?, ?, ?, ?)
                ''', [row['code'], row['name'], row['code_converted'], row['exchange'], row['stock_or_fund']])
            conn.commit()
            added_count = len(new_df)

        if len(update_df) > 0:
            # 使用DuckDB的update语句
            for _, row in update_df.iterrows():
                conn.execute('''
                    UPDATE t_base 
                    SET name = ?, code_converted = ?, exchange = ?
                    WHERE code = ? AND stock_or_fund = 1
                ''', [row['name'], row['code_converted'], row['exchange'], row['code']])
            conn.commit()
            updated_count = len(update_df)
    else:
        # 全量模式：先删除所有，再插入
        conn.execute("DELETE FROM t_base WHERE stock_or_fund = 1")
        for _, row in stock_df.iterrows():
            conn.execute('''
                INSERT INTO t_base (code, name, code_converted, exchange, stock_or_fund)
                VALUES (?, ?, ?, ?, ?)
            ''', [row['code'], row['name'], row['code_converted'], row['exchange'], row['stock_or_fund']])
        conn.commit()
        added_count = len(stock_df)

    print(f"股票数据 - 新增: {added_count}条, 更新: {updated_count}条")
    return added_count, updated_count


def insert_funds(conn, incremental=True):
    """插入基金数据
    incremental: True表示增量模式，只添加新数据并更新已有数据；False表示全量替换
    """
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

    # 获取数据库中已有的基金代码
    existing_codes = set()
    result = conn.execute("SELECT code FROM t_base WHERE stock_or_fund = 2").fetchall()
    for row in result:
        existing_codes.add(row[0])

    # 分离新增和更新的数据
    new_df = fund_df[~fund_df['code'].isin(existing_codes)]
    update_df = fund_df[fund_df['code'].isin(existing_codes)]

    added_count = 0
    updated_count = 0

    if incremental:
        # 增量模式：添加新数据，更新已有数据
        if len(new_df) > 0:
            # 使用DuckDB的insert语句
            for _, row in new_df.iterrows():
                conn.execute('''
                    INSERT INTO t_base (code, name, code_converted, exchange, stock_or_fund)
                    VALUES (?, ?, ?, ?, ?)
                ''', [row['code'], row['name'], row['code_converted'], row['exchange'], row['stock_or_fund']])
            conn.commit()
            added_count = len(new_df)

        if len(update_df) > 0:
            # 使用DuckDB的update语句
            for _, row in update_df.iterrows():
                conn.execute('''
                    UPDATE t_base 
                    SET name = ?, code_converted = ?, exchange = ?
                    WHERE code = ? AND stock_or_fund = 2
                ''', [row['name'], row['code_converted'], row['exchange'], row['code']])
            conn.commit()
            updated_count = len(update_df)
    else:
        # 全量模式：先删除所有，再插入
        conn.execute("DELETE FROM t_base WHERE stock_or_fund = 2")
        for _, row in fund_df.iterrows():
            conn.execute('''
                INSERT INTO t_base (code, name, code_converted, exchange, stock_or_fund)
                VALUES (?, ?, ?, ?, ?)
            ''', [row['code'], row['name'], row['code_converted'], row['exchange'], row['stock_or_fund']])
        conn.commit()
        added_count = len(fund_df)

    print(f"基金数据 - 新增: {added_count}条, 更新: {updated_count}条")
    return added_count, updated_count


def main(incremental=True):
    """主函数
    incremental: True表示增量模式，False表示全量替换
    """
    if incremental:
        print("开始增量更新基础数据...")
    else:
        print("开始全量初始化基础数据...")

    conn = init_db()

    stock_added, stock_updated = insert_stocks(conn, incremental)
    fund_added, fund_updated = insert_funds(conn, incremental)

    result = conn.execute("SELECT COUNT(*) FROM t_base").fetchone()
    print(f"\n表中总数据量: {result[0]}")

    stock_result = conn.execute("SELECT COUNT(*) FROM t_base WHERE stock_or_fund = 1").fetchone()
    fund_result = conn.execute("SELECT COUNT(*) FROM t_base WHERE stock_or_fund = 2").fetchone()
    print(f"股票数量: {stock_result[0]}, 基金数量: {fund_result[0]}")

    print(f"\n更新统计:")
    print(f"  股票 - 新增: {stock_added}, 更新: {stock_updated}")
    print(f"  基金 - 新增: {fund_added}, 更新: {fund_updated}")

    sample = conn.execute("SELECT * FROM t_base ORDER BY stock_or_fund, code LIMIT 5").fetchall()
    print("\n示例数据:")
    for row in sample:
        print(f"  {row}")

    conn.close()
    print("\n数据更新完成!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='初始化或更新基础数据')
    parser.add_argument('--full', action='store_true', help='全量替换模式（默认是增量模式）')
    args = parser.parse_args()
    
    main(incremental=not args.full)
