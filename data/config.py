import os

# PostgreSQL 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'stock_data',
    'user': 'postgres',
    'password': 'postgres'
}

# 数据库连接字符串
DB_CONNECTION_STRING = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['database']} user={DB_CONFIG['user']} password={DB_CONFIG['password']}"

# 检查PostgreSQL连接的函数
def check_postgres_connection():
    """检查PostgreSQL连接是否可用"""
    try:
        import psycopg2
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        conn.close()
        return True
    except Exception as e:
        print(f"PostgreSQL连接失败: {e}")
        print("请确保PostgreSQL服务器已启动，并且配置正确")
        return False
