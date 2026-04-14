import pandas as pd
import requests
import duckdb
from io import StringIO

from akshare.utils.cons import headers


def fund_etf_fund_daily_cn_jzzzl() -> pd.DataFrame:
    """
    东方财富网-天天基金网-基金数据-场内交易基金净值
    https://fund.eastmoney.com/cnjy_jzzzl.html
    :return: 当前交易日的所有场内交易基金净值数据
    :rtype: pandas.DataFrame
    """
    url = "https://fund.eastmoney.com/cnjy_jzzzl.html"
    r = requests.get(url, headers=headers)
    r.encoding = "gb2312"
    temp_df = pd.read_html(StringIO(r.text))[1]
    date_today = temp_df.iloc[0, 6]
    date_yesterday = temp_df.iloc[0, 8]
    temp_df = temp_df.iloc[2:, 3:]
    temp_df.reset_index(inplace=True, drop=True)
    temp_df.columns = [
        "基金代码",
        "基金简称",
        "类型",
        f"{date_today}-单位净值",
        f"{date_today}-累计净值",
        f"{date_yesterday}-单位净值",
        f"{date_yesterday}-累计净值",
        "增长值",
        "增长率",
        "市价",
        "折价率",
    ]
    temp_df["基金简称"] = temp_df["基金简称"].str.replace("行情吧档案", "")
    return temp_df


def save_to_duckdb(df: pd.DataFrame, db_path: str = "data/fund.duckdb"):
    """
    保存数据到 duckdb 数据库
    :param df: 要保存的 DataFrame
    :param db_path: 数据库文件路径
    """
    con = duckdb.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS fund_etf (基金代码 VARCHAR, 基金简称 VARCHAR, 类型 VARCHAR)")
    con.execute("DELETE FROM fund_etf")
    for _, row in df.iterrows():
        con.execute(
            "INSERT INTO fund_etf VALUES (?, ?, ?)",
            [row["基金代码"], row["基金简称"], row["类型"]]
        )
    con.close()


if __name__ == "__main__":
    df = fund_etf_fund_daily_cn_jzzzl()
    print(df)
    save_to_duckdb(df)
    print("\n数据已保存到 duckdb")
