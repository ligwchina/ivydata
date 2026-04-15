import os

# 数据库类型配置: 'postgres' 或 'duckdb'
DB_TYPE = 'duckdb'  # 默认使用DuckDB

# PostgreSQL 数据库配置
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'stock_data',
    'user': 'postgres',
    'password': 'postgres'
}

# 数据库连接字符串
POSTGRES_CONNECTION_STRING = f"host={POSTGRES_CONFIG['host']} port={POSTGRES_CONFIG['port']} dbname={POSTGRES_CONFIG['database']} user={POSTGRES_CONFIG['user']} password={POSTGRES_CONFIG['password']}"

# DuckDB 数据库配置
DUCKDB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_data.duckdb')

# 检查PostgreSQL连接的函数
def check_postgres_connection():
    """检查PostgreSQL连接是否可用"""
    try:
        import psycopg2
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        conn.close()
        return True
    except Exception as e:
        print(f"PostgreSQL连接失败: {e}")
        print("请确保PostgreSQL服务器已启动，并且配置正确")
        return False

# 检查DuckDB连接的函数
def check_duckdb_connection():
    """检查DuckDB连接是否可用"""
    try:
        import duckdb
        conn = duckdb.connect(DUCKDB_PATH)
        conn.close()
        return True
    except Exception as e:
        print(f"DuckDB连接失败: {e}")
        print("请确保DuckDB已安装")
        return False
