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
    start_time='20260411',
    end_time='',
    count=0,
    dividend_type='none',
    period='1d',
    fill_data=True
)

print(raw_data)