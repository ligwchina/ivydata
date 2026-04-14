import duckdb
import os
import pandas as pd
from datetime import datetime

DB_PATH = r'D:\dev\ai\ivydata\db\ivy.duckdb'
OUTPUT_DIR = r'D:\dev\ai\ivydata\data'


def get_db_connection():
    """获取数据库连接"""
    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
    except Exception:
        import tempfile
        import shutil
        temp_db = os.path.join(tempfile.gettempdir(), 'ivy_temp.duckdb')
        shutil.copy2(DB_PATH, temp_db)
        conn = duckdb.connect(temp_db, read_only=True)
    return conn


def check_missing_kline():
    """检查哪些股票和基金没有获取到K线数据"""
    conn = get_db_connection()

    all_stocks = conn.execute("""
        SELECT code, name, code_converted, stock_or_fund
        FROM t_base
        WHERE stock_or_fund = 1
    """).fetchdf()

    all_funds = conn.execute("""
        SELECT code, name, code_converted, stock_or_fund
        FROM t_base
        WHERE stock_or_fund = 2
    """).fetchdf()

    print(f"数据库中股票总数: {len(all_stocks)}")
    print(f"数据库中基金总数: {len(all_funds)}")

    funds_with_kline = conn.execute("""
        SELECT DISTINCT code
        FROM t_day_k
    """).fetchdf()

    codes_with_kline = set(funds_with_kline['code'].tolist())
    print(f"有K线数据的代码数量: {len(codes_with_kline)}")

    stocks_without_kline = all_stocks[~all_stocks['code'].isin(codes_with_kline)]
    funds_without_kline = all_funds[~all_funds['code'].isin(codes_with_kline)]

    print(f"没有K线数据的股票数量: {len(stocks_without_kline)}")
    print(f"没有K线数据的基金数量: {len(funds_without_kline)}")

    conn.close()

    return stocks_without_kline, funds_without_kline


def save_to_txt(stocks_df, funds_df, output_path):
    """将没有K线数据的股票和基金保存到txt文件"""
    total_count = len(stocks_df) + len(funds_df)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"没有K线数据的股票和基金列表 (共{total_count}条)\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n")

        if len(stocks_df) > 0:
            f.write(f"\n【股票】共{len(stocks_df)}条\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'代码':<10} {'转换代码':<12} {'名称'}\n")
            f.write("-" * 70 + "\n")
            for _, row in stocks_df.iterrows():
                f.write(f"{row['code']:<10} {row['code_converted']:<12} {row['name']}\n")

        if len(funds_df) > 0:
            f.write(f"\n【基金】共{len(funds_df)}条\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'代码':<10} {'转换代码':<12} {'名称'}\n")
            f.write("-" * 70 + "\n")
            for _, row in funds_df.iterrows():
                f.write(f"{row['code']:<10} {row['code_converted']:<12} {row['name']}\n")


def main():
    print("=" * 50)
    print("检查没有K线数据的股票和基金")
    print("=" * 50)

    stocks_without_kline, funds_without_kline = check_missing_kline()

    output_filename = f"missing_kline_{datetime.now().strftime('%Y%m%d')}.txt"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    save_to_txt(stocks_without_kline, funds_without_kline, output_path)

    print(f"\n结果已保存到: {output_path}")

    if len(stocks_without_kline) > 0:
        print("\n没有K线数据的股票 (前10条):")
        print(stocks_without_kline.head(10).to_string(index=False))

    if len(funds_without_kline) > 0:
        print("\n没有K线数据的基金 (前10条):")
        print(funds_without_kline.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
