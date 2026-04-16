#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比 ETF 和东方财富基金数据
"""

import sys
import requests
from io import StringIO

sys.stdout.reconfigure(encoding='utf-8')

import akshare as ak
import pandas as pd

print("=" * 50)
print("对比 ETF 和东方财富基金数据")
print("=" * 50)

# 获取 ETF 数据
etf_codes = set()
try:
    fund_etf_df = ak.fund_etf_spot_ths()
    if fund_etf_df is not None and len(fund_etf_df) > 0:
        for _, row in fund_etf_df.iterrows():
            code = str(row.get('基金代码', ''))
            if code:
                etf_codes.add(code)
        print(f"ETF 基金数量: {len(etf_codes)}")
except Exception as e:
    print(f"获取 ETF 失败: {e}")

# 获取东方财富数据
em_codes = set()
try:
    from akshare.utils.cons import headers
    url = "https://fund.eastmoney.com/cnjy_jzzzl.html"
    r = requests.get(url, headers=headers, timeout=30)
    r.encoding = "gb2312"
    tables = pd.read_html(StringIO(r.text))
    if len(tables) >= 2:
        temp_df = tables[1]
        temp_df = temp_df.iloc[2:].copy()
        temp_df = temp_df[[3, 4, 5]].reset_index(drop=True)
        temp_df.columns = ["基金代码", "基金简称", "类型"]
        
        for _, row in temp_df.iterrows():
            code = str(row.get('基金代码', ''))
            if code:
                em_codes.add(code)
        print(f"东方财富基金数量: {len(em_codes)}")
except Exception as e:
    print(f"获取东方财富失败: {e}")

# 对比
common = etf_codes & em_codes
only_etf = etf_codes - em_codes
only_em = em_codes - etf_codes

print(f"\n对比结果:")
print(f"  共同基金: {len(common)}")
print(f"  仅 ETF: {len(only_etf)}")
print(f"  仅东方财富: {len(only_em)}")
print(f"  去重后总计: {len(etf_codes | em_codes)}")

print(f"\n仅东方财富的基金示例（前10个）:")
for i, code in enumerate(list(only_em)[:10]):
    print(f"  {code}")
