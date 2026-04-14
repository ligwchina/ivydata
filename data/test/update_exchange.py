import duckdb
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_converter import convert_code, get_exchange

DB_PATH = r'D:\dev\ai\ivydata\db\ivy.duckdb'


def update_exchange():
    """重新生成t_base表中的exchange字段"""
    try:
        conn = duckdb.connect(DB_PATH, read_only=False)
    except Exception:
        import tempfile
        import shutil
        temp_db = os.path.join(tempfile.gettempdir(), 'ivy_temp.duckdb')
        shutil.copy2(DB_PATH, temp_db)
        conn = duckdb.connect(temp_db, read_only=False)

    all_codes = conn.execute("SELECT code FROM t_base").fetchall()

    print(f"开始更新 {len(all_codes)} 条记录的exchange字段...")

    for row in all_codes:
        code = row[0]
        exchange = get_exchange(code)
        conn.execute("UPDATE t_base SET exchange = ? WHERE code = ?", [exchange, code])

    result = conn.execute("SELECT exchange, COUNT(*) FROM t_base GROUP BY exchange").fetchall()
    print("\n更新后的交易所分布:")
    for row in result:
        print(f"  {row[0]}: {row[1]} 条")

    conn.close()
    print("\nExchange字段更新完成!")


if __name__ == "__main__":
    update_exchange()
