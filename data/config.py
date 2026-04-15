import os

# DuckDB 数据库配置
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_data.duckdb')

# 检查DuckDB连接的函数
def check_duckdb_connection():
    """检查DuckDB连接是否可用"""
    try:
        import duckdb
        conn = duckdb.connect(DB_PATH)
        conn.close()
        return True
    except Exception as e:
        print(f"DuckDB连接失败: {e}")
        print("请确保DuckDB已安装")
        return False
