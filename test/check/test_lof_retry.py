#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 LOF 基金数据获取
"""

import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

import akshare as ak

print("测试 LOF 基金数据获取...")

# 尝试获取 LOF 基金，增加重试机制
max_retries = 3
for attempt in range(max_retries):
    try:
        print(f"尝试 {attempt + 1}/{max_retries}...")
        fund_lof_df = ak.fund_lof_spot_em()
        print(f"成功获取 {len(fund_lof_df)} 只LOF基金")
        print("前5只:")
        for i, row in fund_lof_df.head().iterrows():
            print(f"  {row.get('代码', '')} - {row.get('名称', '')}")
        break
    except Exception as e:
        print(f"尝试 {attempt + 1} 失败: {e}")
        if attempt < max_retries - 1:
            print("等待 2 秒后重试...")
            time.sleep(2)
        else:
            print("所有尝试都失败了")
