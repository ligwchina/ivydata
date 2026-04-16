#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基金数据抓取功能
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data'))

from base_data_with_duckdb import fetch_fund_info

if __name__ == "__main__":
    print("=" * 50)
    print("测试基金数据抓取功能")
    print("=" * 50)
    
    fund_list = fetch_fund_info()
    
    print(f"\n" + "=" * 50)
    print(f"测试完成! 共获取 {len(fund_list)} 只基金")
    print("=" * 50)
    
    print("\n前10只基金:")
    for i, fund in enumerate(fund_list[:10]):
        print(f"  {i+1}. {fund['code']} - {fund['name']}")
