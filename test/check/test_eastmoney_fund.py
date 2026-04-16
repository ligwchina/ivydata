#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基金数据抓取功能 - 直接运行
"""

import sys
import os
import requests
from io import StringIO

sys.stdout.reconfigure(encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data'))

import akshare as ak
import pandas as pd

def test_eastmoney():
    """测试东方财富基金数据"""
    print("\n" + "="*50)
    print("测试东方财富基金数据")
    print("="*50)
    try:
        from akshare.utils.cons import headers
        url = "https://fund.eastmoney.com/cnjy_jzzzl.html"
        r = requests.get(url, headers=headers, timeout=30)
        r.encoding = "gb2312"
        temp_df = pd.read_html(StringIO(r.text))[1]
        temp_df = temp_df.iloc[2:].copy()
        temp_df = temp_df[[3, 4, 5]].reset_index(drop=True)
        temp_df.columns = ["基金代码", "基金简称", "类型"]
        temp_df["基金简称"] = temp_df["基金简称"].str.replace("行情吧档案", "")
        
        print(f"成功获取 {len(temp_df)} 只基金")
        print("\n前10只基金:")
        for i, row in temp_df.head(10).iterrows():
            print(f"  {i+1}. {row['基金代码']} - {row['基金简称']}")
        
        return temp_df
    except Exception as e:
        print(f"获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_eastmoney()
