#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试东方财富基金数据获取
"""

import sys
import requests
from io import StringIO
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

print("开始测试东方财富基金数据...")

try:
    from akshare.utils.cons import headers
    url = "https://fund.eastmoney.com/cnjy_jzzzl.html"
    print(f"请求URL: {url}")
    
    r = requests.get(url, headers=headers, timeout=30)
    print(f"响应状态码: {r.status_code}")
    print(f"响应编码: {r.encoding}")
    
    r.encoding = "gb2312"
    tables = pd.read_html(StringIO(r.text))
    print(f"找到 {len(tables)} 个表格")
    
    if len(tables) >= 2:
        temp_df = tables[1]
        print(f"表格1形状: {temp_df.shape}")
        print(f"表格1列名: {temp_df.columns.tolist()}")
        print(f"\n原始数据前5行:")
        print(temp_df.head())
        
        temp_df = temp_df.iloc[2:].copy()
        temp_df = temp_df[[3, 4, 5]].reset_index(drop=True)
        temp_df.columns = ["基金代码", "基金简称", "类型"]
        temp_df["基金简称"] = temp_df["基金简称"].str.replace("行情吧档案", "")
        
        print(f"\n处理后数据形状: {temp_df.shape}")
        print(f"成功获取 {len(temp_df)} 只基金")
        
        print("\n前10只基金:")
        for i, row in temp_df.head(10).iterrows():
            print(f"  {i+1}. {row['基金代码']} - {row['基金简称']}")
    else:
        print("没有找到足够的表格")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
