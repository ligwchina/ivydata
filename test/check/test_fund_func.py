#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 fund_etf_spot_ths 函数
"""

import sys
import inspect
import akshare as ak

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

print("=" * 50)
print("测试 fund_etf_spot_ths 函数")
print("=" * 50)

# 查看函数签名
print("\n--- 函数签名 ---")
print(inspect.signature(ak.fund_etf_spot_ths))

# 查看函数文档
print("\n--- 函数文档 ---")
print(ak.fund_etf_spot_ths.__doc__)

# 尝试不带参数调用
print("\n--- 尝试不带参数调用 ---")
try:
    result = ak.fund_etf_spot_ths()
    print(f"✅ 成功！返回 {len(result)} 条数据")
    print(f"列名: {list(result.columns)}")
    print(f"\n前5条数据:\n{result.head()}")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    print(f"\n详细错误:\n{traceback.format_exc()}")

print("\n" + "=" * 50)
