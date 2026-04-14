import akshare as ak
import pandas as pd
from datetime import datetime

def get_trade_dates_since(start_date: str) -> pd.Series:
    """
    获取从指定日期到今天的所有A股交易日
    
    参数:
        start_date (str): 起始日期，格式如 '2024-01-01' 或 '20240101'
    
    返回:
        pd.Series: 交易日列表（datetime格式）
    """
    # 1. 获取新浪财经提供的全部历史交易日历
    trade_cal = ak.tool_trade_date_hist_sina() 

    # 2. 转换日期格式（确保为datetime）
    trade_cal["trade_date"] = pd.to_datetime(trade_cal["trade_date"])
    start_date = pd.to_datetime(start_date)
    today = pd.to_datetime(datetime.today().strftime("%Y-%m-%d"))

    # 3. 筛选 [起始日期, 今天] 区间的交易日
    mask = (trade_cal["trade_date"] >= start_date) & (trade_cal["trade_date"] <= today)
    trade_dates = trade_cal.loc[mask, "trade_date"].reset_index(drop=True)

    return trade_dates

# ------------------- 示例调用 -------------------
if __name__ == "__main__":
    # 从2025年1月1日到今天的交易日
    dates = get_trade_dates_since(start_date="2026-03-23")
    
    print(f"从2026-03-23到今天的交易日共 {len(dates)} 天：")
    print(dates.dt.strftime("%Y-%m-%d").tolist())