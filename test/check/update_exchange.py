import psycopg2
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from code_converter import convert_code, get_exchange

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF',
    'database': 'ivydata'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def update_exchange():
    """重新生成base_data表中的exchange字段"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT code FROM base_data")
    all_codes = cur.fetchall()

    print(f"开始更新 {len(all_codes)} 条记录的exchange字段...")

    for row in all_codes:
        code = row[0]
        exchange = get_exchange(code)
        cur.execute("UPDATE base_data SET exchange = %s WHERE code = %s", [exchange, code])

    cur.execute("SELECT exchange, COUNT(*) FROM base_data GROUP BY exchange")
    result = cur.fetchall()
    print("\n更新后的交易所分布:")
    for row in result:
        print(f"  {row[0]}: {row[1]} 条")

    conn.commit()
    cur.close()
    conn.close()
    print("\nExchange字段更新完成!")


if __name__ == "__main__":
    update_exchange()
