import duckdb

DB_PATH = r'D:\dev\ai\ivydata\db\ivy.duckdb'


def clear_tables():
    """清空t_day_k表和t_grab_record表"""
    conn = duckdb.connect(DB_PATH, read_only=False)

    day_k_count = conn.execute("SELECT COUNT(*) FROM t_day_k").fetchone()[0]
    grab_record_count = conn.execute("SELECT COUNT(*) FROM t_grab_record").fetchone()[0]

    print(f"t_day_k表当前数据量: {day_k_count}")
    print(f"t_grab_record表当前数据量: {grab_record_count}")

    conn.execute("DELETE FROM t_day_k")
    conn.execute("DELETE FROM t_grab_record")

    print("\n表已清空!")

    conn.close()


if __name__ == "__main__":
    clear_tables()
