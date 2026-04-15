import psycopg2

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF',
    'database': 'ivydata'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def clear_tables():
    """清空kline_data表和grab_record表"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM kline_data")
    kline_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM grab_record")
    grab_record_count = cur.fetchone()[0]

    print(f"kline_data表当前数据量: {kline_count}")
    print(f"grab_record表当前数据量: {grab_record_count}")

    cur.execute("DELETE FROM kline_data")
    cur.execute("DELETE FROM grab_record")

    conn.commit()
    print("\n表已清空!")

    cur.close()
    conn.close()


if __name__ == "__main__":
    clear_tables()
