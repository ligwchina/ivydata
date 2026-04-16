#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 akshare 的各种基金数据接口
"""

import sys
import akshare as ak

sys.stdout.reconfigure(encoding='utf-8')

def test_fund_etf_spot_ths():
    """测试 ETF 基金"""
    print("\n" + "="*50)
    print("测试 fund_etf_spot_ths - ETF基金")
    print("="*50)
    try:
        df = ak.fund_etf_spot_ths()
        print(f"成功获取 {len(df)} 条ETF基金数据")
        print("列名:", df.columns.tolist())
        print("\n前5条数据:")
        print(df.head())
        return df
    except Exception as e:
        print(f"失败: {e}")
        return None

def test_fund_lof_spot_em():
    """测试 LOF 基金"""
    print("\n" + "="*50)
    print("测试 fund_lof_spot_em - LOF基金")
    print("="*50)
    try:
        df = ak.fund_lof_spot_em()
        print(f"成功获取 {len(df)} 条LOF基金数据")
        print("列名:", df.columns.tolist())
        print("\n前5条数据:")
        print(df.head())
        return df
    except Exception as e:
        print(f"失败: {e}")
        return None

def test_fund_graded_spot_em():
    """测试分级基金"""
    print("\n" + "="*50)
    print("测试 fund_graded_spot_em - 分级基金")
    print("="*50)
    try:
        df = ak.fund_graded_spot_em()
        print(f"成功获取 {len(df)} 条分级基金数据")
        print("列名:", df.columns.tolist())
        print("\n前5条数据:")
        print(df.head())
        return df
    except Exception as e:
        print(f"失败: {e}")
        return None

def test_fund_name_em():
    """测试基金列表"""
    print("\n" + "="*50)
    print("测试 fund_name_em - 基金列表")
    print("="*50)
    try:
        df = ak.fund_name_em()
        print(f"成功获取 {len(df)} 条基金数据")
        print("列名:", df.columns.tolist())
        print("\n前5条数据:")
        print(df.head())
        return df
    except Exception as e:
        print(f"失败: {e}")
        return None

if __name__ == "__main__":
    print("开始测试 akshare 基金数据接口...")
    
    etf_df = test_fund_etf_spot_ths()
    lof_df = test_fund_lof_spot_em()
    graded_df = test_fund_graded_spot_em()
    # name_df = test_fund_name_em()  # 这个可能数据量太大
    
    print("\n" + "="*50)
    print("测试完成!")
    print("="*50)
