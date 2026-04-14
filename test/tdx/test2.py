import duckdb
import os
import pandas as pd
import sys

# 1. 定义通达信安装根目录
tdx_install_path = r"D:\new_tdx64"  # 请修改为你自己的通达信路径

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

# 数据库路径
db_path = r'D:\dev\ai\ivydata\db\fund.duckdb'

# 确保目录存在
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# 连接DuckDB数据库（只读模式检查，如果文件被占用则使用临时文件）
try:
    conn = duckdb.connect(db_path)
except Exception as e:
    print(f"警告：无法直接连接数据库，可能是文件被占用: {e}")
    # 使用临时文件方式
    temp_db_path = db_path.replace('.duckdb', '_temp.duckdb')
    conn = duckdb.connect(temp_db_path)
    print(f"使用临时数据库: {temp_db_path}")

# 创建表（如果不存在）
create_table_sql = """
CREATE TABLE IF NOT EXISTS fund_etf_day_k (
    code VARCHAR,
    date DATE,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    amount DOUBLE,
    PRIMARY KEY (code, date)
)
"""
conn.execute(create_table_sql)

# 准备数据
data_to_insert = df[['code', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount']].copy()

# 清空该股票的旧数据，避免重复
conn.execute(f"DELETE FROM fund_etf_day_k WHERE code = '{STOCK_CODE}'")

# 插入数据
conn.execute("""
    INSERT INTO fund_etf_day_k (code, date, open, high, low, close, volume, amount)
    SELECT code, date, open, high, low, close, volume, amount FROM data_to_insert
""")

print(f"成功插入{len(data_to_insert)}条数据到fund_etf_day_k表")

# 验证数据
result = conn.execute(f"SELECT COUNT(*) FROM fund_etf_day_k WHERE code = '{STOCK_CODE}'").fetchone()
print(f"表中{STOCK_CODE}的数据条数: {result[0]}")

conn.close()
tq.close()
