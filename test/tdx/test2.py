import psycopg2
import os
import pandas as pd
import sys

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF',
    'database': 'ivydata'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# 1. 定义通达信安装根目录
tdx_install_path = r"D:\new_tdx64"

# 2. 拼接出 PYPlugins/user 的绝对路径
pyplugins_user_path = os.path.join(tdx_install_path, "PYPlugins", "user")

# 3. 将该路径插入到 sys.path 的第一位，确保优先加载
sys.path.insert(0, pyplugins_user_path)

# 4. 现在可以愉快地导入了
from tqcenter import tq

# 股票代码
STOCK_CODE = '513050'
STOCK_CODE_FULL = f'{STOCK_CODE}.SH'

tq.initialize(__file__)

# 获取513050的日K数据
raw_data = tq.get_market_data(
    field_list=[],
    stock_list=[STOCK_CODE_FULL],
    start_time='',
    end_time='',
    count=0,
    dividend_type='none',
    period='1d',
    fill_data=True
)

# 原始数据是字典，每个键对应一个DataFrame（列是股票代码，索引是日期）
# 需要将其转换为标准格式
if isinstance(raw_data, dict):
    # 获取日期索引（从任意一个DataFrame中获取）
    first_key = list(raw_data.keys())[0]
    first_df = raw_data[first_key]
    dates = first_df.index

    # 获取数据中的股票代码列名（可能是带后缀的格式）
    stock_columns = first_df.columns.tolist()
    actual_code = stock_columns[0] if stock_columns else STOCK_CODE_FULL

    # 构建新的DataFrame
    df = pd.DataFrame({
        'code': STOCK_CODE,
        'date': dates,
        'open': raw_data['Open'][actual_code].values,
        'high': raw_data['High'][actual_code].values,
        'low': raw_data['Low'][actual_code].values,
        'close': raw_data['Close'][actual_code].values,
        'volume': raw_data['Volume'][actual_code].values,
        'amount': raw_data['Amount'][actual_code].values,
    })
else:
    df = raw_data

print(f"获取到{len(df)}条数据")
print(df.head())

# 连接 PostgreSQL 数据库
conn = get_db_connection()
cur = conn.cursor()

# 创建表（如果不存在）
cur.execute("""
    CREATE TABLE IF NOT EXISTS fund_etf_day_k (
        id SERIAL PRIMARY KEY,
        code VARCHAR(20) NOT NULL,
        date DATE NOT NULL,
        open NUMERIC(18, 4) NOT NULL,
        high NUMERIC(18, 4) NOT NULL,
        low NUMERIC(18, 4) NOT NULL,
        close NUMERIC(18, 4) NOT NULL,
        volume BIGINT NOT NULL,
        amount NUMERIC(18, 4) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(code, date)
    )
""")

# 清空该股票的旧数据，避免重复
cur.execute("DELETE FROM fund_etf_day_k WHERE code = %s", (STOCK_CODE,))

# 准备数据
for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO fund_etf_day_k (code, date, open, high, low, close, volume, amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (code, date) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            amount = EXCLUDED.amount
    """, (row['code'], row['date'], row['open'], row['high'], row['low'], row['close'], row['volume'], row['amount']))

conn.commit()

# 验证数据
cur.execute("SELECT COUNT(*) FROM fund_etf_day_k WHERE code = %s", (STOCK_CODE,))
result = cur.fetchone()
print(f"表中{STOCK_CODE}的数据条数: {result[0]}")

cur.close()
conn.close()
tq.close()
