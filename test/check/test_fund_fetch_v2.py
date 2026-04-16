#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基金数据抓取功能 - 完整版
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 直接定义简化的获取函数
import akshare as ak
import requests
from io import StringIO
import pandas as pd

def fetch_fund_info():
    """获取基金列表"""
    print("正在获取基金列表...")

    fund_list = []
    fund_codes = set()  # 用于去重

    # 方式1: 获取ETF基金 (akshare API)
    try:
        fund_etf_df = ak.fund_etf_spot_ths()
        if fund_etf_df is not None and len(fund_etf_df) > 0:
            for _, row in fund_etf_df.iterrows():
                code = str(row.get('基金代码', ''))
                name = str(row.get('基金名称', ''))
                if code and code not in fund_codes:
                    fund_list.append({'code': code, 'name': name})
                    fund_codes.add(code)
            print(f"成功获取 {len(fund_etf_df)} 只ETF基金")
    except Exception as e:
        print(f"警告: 获取ETF基金失败: {e}")

    # 方式2: 获取LOF基金 (akshare API)
    try:
        fund_lof_df = ak.fund_lof_spot_em()
        if fund_lof_df is not None and len(fund_lof_df) > 0:
            for _, row in fund_lof_df.iterrows():
                code = str(row.get('代码', ''))
                name = str(row.get('名称', ''))
                if code and code not in fund_codes:
                    fund_list.append({'code': code, 'name': name})
                    fund_codes.add(code)
            print(f"成功获取 {len(fund_lof_df)} 只LOF基金")
    except Exception as e:
        print(f"警告: 获取LOF基金失败: {e}")

    # 方式3: 从东方财富网页面爬取更全面的基金数据
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

        count_before = len(fund_list)
        for _, row in temp_df.iterrows():
            code = str(row.get('基金代码', ''))
            name = str(row.get('基金简称', ''))
            if code and code not in fund_codes:
                fund_list.append({'code': code, 'name': name})
                fund_codes.add(code)

        count_added = len(fund_list) - count_before
        if count_added > 0:
            print(f"从东方财富成功获取 {len(temp_df)} 只基金，新增 {count_added} 只")
    except Exception as e:
        print(f"警告: 从东方财富网页获取基金失败: {e}")

    print(f"总计获取 {len(fund_list)} 只基金信息（去重后）")
    return fund_list


if __name__ == "__main__":
    print("=" * 50)
    print("测试基金数据抓取功能")
    print("=" * 50)

    fund_list = fetch_fund_info()

    print(f"\n" + "=" * 50)
    print(f"测试完成! 共获取 {len(fund_list)} 只基金")
    print("=" * 50)

    print("\n前20只基金:")
    for i, fund in enumerate(fund_list[:20]):
        print(f"  {i+1}. {fund['code']} - {fund['name']}")
