import os
import sys

# 1. 定义通达信安装根目录
tdx_install_path = r"D:\new_tdx64"  # 请修改为你自己的通达信路径

# 2. 拼接出 PYPlugins/user 的绝对路径
pyplugins_user_path = os.path.join(tdx_install_path, "PYPlugins", "user")

# 3. 将该路径插入到 sys.path 的第一位，确保优先加载
sys.path.insert(0, pyplugins_user_path)

# 4. 现在可以愉快地导入了
from tqcenter import tq

tq.initialize(__file__)
stock_list = tq.get_stock_list()
print(stock_list)

# stock_list2 = tq.get_stock_list('16')
# print(stock_list2)
