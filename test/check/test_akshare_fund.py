#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 akshare 基金数据接口
"""

import sys
import akshare as ak

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

print("=" * 50)
print("测试 akshare 基金数据接口")
print("=" * 50)

# 尝试多个基金接口
fund_functions = [
    ('fund_etf_spot_ths', 'ak.fund_etf_spot_ths'),
    ('fund_etf_spot_sina', 'ak.fund_etf_spot_sina'),
    ('fund_etf_spot_sohu', 'ak.fund_etf_spot_sohu'),
    ('fund_etf_spot_eastmoney', 'ak.fund_etf_spot_eastmoney'),
    ('fund_etf_spot', 'ak.fund_etf_spot'),
    ('fund_info_index_em', 'ak.fund_info_index_em'),
    ('fund_info_etf_em', 'ak.fund_info_etf_em'),
    ('fund_info_lof_em', 'ak.fund_info_lof_em'),
    ('fund_em_info_lof', 'ak.fund_em_info_lof'),
    ('fund_em_etf_spot', 'ak.fund_em_etf_spot'),
]

print("\n开始测试...")

for name, func_str in fund_functions:
    print(f"\n--- 测试 {name} ---")
    try:
        func = eval(func_str)
        if func is not None and len(func) > 0:
            print(f"✅ 成功，返回 {len(func)} 条数据")
            print(f"列名: {list(func.columns)}")
            print(f"前3条数据:\n{func.head(3)}")
            break
    except Exception as e:
        print(f"❌ 失败: {e}")

print("\n" + "=" * 50)
print("测试完成")
print("=" * 50)
