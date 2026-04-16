import duckdb

DB_PATH = 'D:\\dev\\ai\\ivydata\\db\\ivy.duckdb'

def get_db_connection():
    return duckdb.connect(DB_PATH)


def clear_tables():
    """清空kline_data表和grab_record表"""
    conn = get_db_connection()

    kline_count = conn.execute("SELECT COUNT(*) FROM kline_data").fetchone()[0]
    grab_record_count = conn.execute("SELECT COUNT(*) FROM grab_record").fetchone()[0]

    print(f"kline_data表当前数据量: {kline_count}")
    print(f"grab_record表当前数据量: {grab_record_count}")

    conn.execute("DELETE FROM kline_data")
    conn.execute("DELETE FROM grab_record")

    conn.commit()
    print("\n表已清空!")

    conn.close()


if __name__ == "__main__":
    clear_tables()
