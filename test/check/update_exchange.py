import duckdb
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_converter import convert_code, get_exchange

DB_PATH = 'D:\\dev\\ai\\ivydata\\db\\ivy.duckdb'

def get_db_connection():
    return duckdb.connect(DB_PATH)


def update_exchange():
    """重新生成base_data表中的exchange字段"""
    conn = get_db_connection()

    all_codes = conn.execute("SELECT code FROM base_data").fetchall()

    print(f"开始更新 {len(all_codes)} 条记录的exchange字段...")

    for row in all_codes:
        code = row[0]
        exchange = get_exchange(code)
        conn.execute("UPDATE base_data SET exchange = ? WHERE code = ?", [exchange, code])

    result = conn.execute("SELECT exchange, COUNT(*) FROM base_data GROUP BY exchange").fetchall()
    print("\n更新后的交易所分布:")
    for row in result:
        print(f"  {row[0]}: {row[1]} 条")

    conn.commit()
    conn.close()
    print("\nExchange字段更新完成!")


if __name__ == "__main__":
    update_exchange()
