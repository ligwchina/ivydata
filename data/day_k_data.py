#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K线数据增量抓取程序（直接写入PostgreSQL）
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from datetime import datetime
import traceback

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../test/base'))
from data_num import get_trade_dates_since

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helper import ensure_all_tables, update_sys_option

tdx_install_path = r"D:\new_tdx64"
pyplugins_user_path = os.path.join(tdx_install_path, "PYPlugins", "user")
sys.path.insert(0, pyplugins_user_path)

from tqcenter import tq

POSTGRESQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'ivydata',
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF'
}


def get_db_connection():
    return psycopg2.connect(**POSTGRESQL_CONFIG)


def ensure_base_data_exists():
    """检查 base_data 表是否存在"""
    try:
        log("检查 base_data 表...")
        
        pg_conn = get_db_connection()
        pg_cursor = pg_conn.cursor()
        
        pg_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'base_data'
            )
        """)
        base_data_exists = pg_cursor.fetchone()[0]
        
        if not base_data_exists:
            log("base_data 表不存在，请先运行 base_data.py 创建基础数据")
            pg_cursor.close()
            pg_conn.close()
            raise SystemExit(1)
        
        pg_cursor.close()
        pg_conn.close()
        
        log("检查其他表...")
        ensure_all_tables()
        
        log("数据库表结构检查完成")
    except SystemExit:
        raise
    except Exception as e:
        print_error(f"初始化数据库失败\n详细信息: {e}")
        raise SystemExit(1)


def ensure_log_dir():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def log(message, end='\n'):
    print(message, end=end)
    ensure_log_dir()
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', f'kline_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + end)


def print_error(message):
    log(f"\n{'='*50}")
    log(f"错误: {message}")
    log(f"{'='*50}\n")


def print_warning(message):
    log(f"\n警告: {message}\n")


def get_all_base_data_codes():
    """获取所有基础数据代码"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT code, code_converted FROM base_data ORDER BY code")
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        print_error(f"查询基础数据失败\n详细信息: {e}")
        raise SystemExit(1)


def get_latest_date_for_code(code):
    """获取指定代码的最新K线日期"""
    start = datetime.now()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(date) FROM kline_data WHERE code = %s", (code,))
        result = cursor.fetchone()
        conn.close()
        elapsed = (datetime.now() - start).total_seconds()
        return result[0], elapsed
    except Exception as e:
        print_warning(f"查询最新日期失败: {e}")
        return None, 0


def get_day_k_data(stock_code, stock_code_full, start_date='', end_date=''):
    """获取K线数据"""
    start = datetime.now()
    try:
        log(f"  [TQ] 开始获取数据, code={stock_code}, start_date={start_date or '全量'}")
        tq_start = datetime.now()
        raw_data = tq.get_market_data(
            field_list=[],
            stock_list=[stock_code_full],
            start_time=start_date,
            end_time=end_date,
            count=0,
            dividend_type='none',
            period='1d',
            fill_data=True
        )
        tq_elapsed = (datetime.now() - tq_start).total_seconds()
        log(f"  [TQ] tq.get_market_data 耗时: {tq_elapsed:.2f}秒")

        if raw_data is None:
            return None, "通达信返回空数据"

        if not isinstance(raw_data, dict):
            return None, f"数据类型异常: {type(raw_data)}"

        if len(raw_data) == 0:
            return None, "通达信返回空字典"

        first_key = list(raw_data.keys())[0]
        first_df = raw_data[first_key]

        if first_df is None or len(first_df) == 0:
            return None, "数据为空"

        dates = first_df.index
        stock_columns = first_df.columns.tolist()
        actual_code = stock_columns[0] if stock_columns else stock_code_full

        df_start = datetime.now()
        df = pd.DataFrame({
            'code': stock_code,
            'date': dates,
            'open': raw_data['Open'][actual_code].values,
            'high': raw_data['High'][actual_code].values,
            'low': raw_data['Low'][actual_code].values,
            'close': raw_data['Close'][actual_code].values,
            'volume': raw_data['Volume'][actual_code].values,
            'amount': raw_data['Amount'][actual_code].values,
        })
        df_elapsed = (datetime.now() - df_start).total_seconds()
        log(f"  [TQ] DataFrame构建耗时: {df_elapsed:.2f}秒, 数据条数: {len(df)}")

        total_elapsed = (datetime.now() - start).total_seconds()
        log(f"  [TQ] 总耗时: {total_elapsed:.2f}秒")
        return df, None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        return None, error_msg


def insert_to_postgresql(df):
    """直接插入数据到PostgreSQL"""
    try:
        if df is None or len(df) == 0:
            return 0

        df['date'] = pd.to_datetime(df['date']).dt.date

        insert_data = []
        for _, row in df.iterrows():
            insert_data.append((
                row['code'],
                row['date'],
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                int(row['volume']),
                row['amount']
            ))

        if not insert_data:
            return 0

        pg_conn = get_db_connection()
        pg_cursor = pg_conn.cursor()

        step_start = datetime.now()
        execute_values(pg_cursor, """
            INSERT INTO kline_data (code, date, open, high, low, close, volume, amount)
            VALUES %s
            ON CONFLICT (code, date) DO NOTHING
        """, insert_data)
        pg_conn.commit()
        log(f"  [PG插入] 耗时: {(datetime.now() - step_start).total_seconds():.2f}秒, 插入 {len(insert_data)} 条")

        inserted_count = len(insert_data)

        pg_cursor.close()
        pg_conn.close()

        return inserted_count
    except Exception as e:
        print_error(f"插入PostgreSQL失败\n详细信息: {e}")
        raise SystemExit(1)


def main():
    log("=" * 50)
    log("K线数据增量抓取程序启动（直接写入PostgreSQL版）")
    log("=" * 50)

    start_time = datetime.now()

    try:
        ensure_base_data_exists()

        tq.initialize(__file__)
        log("TQ数据接口初始化成功，使用路径: D:\\dev\\ai\\ivydata\\data\\day_k_data_with_duckdb.py")
    except Exception as e:
        log(f"TQ数据接口初始化失败: {e}")
        raise SystemExit(1)

    try:
        codes = get_all_base_data_codes()

        log(f"\n总代码数量: {len(codes)}")

        if not codes:
            log("没有代码需要处理")
            raise SystemExit(0)

        log("\n" + "=" * 50)
        log("开始获取数据...")
        log("=" * 50)

        success_count = 0
        fail_count = 0
        skip_count = 0
        total_records = 0

        for i, (code, code_converted) in enumerate(codes):
            loop_start = datetime.now()
            log(f"\n[{i+1}/{len(codes)}] 正在处理: {code}")

            step_start = datetime.now()
            latest_date, db_elapsed = get_latest_date_for_code(code)
            log(f"  [步骤1] 查询最新日期耗时: {db_elapsed:.2f}秒")

            if latest_date:
                start_date_str = latest_date.strftime('%Y%m%d')
                log(f"  已存在数据，最新日期: {start_date_str}")

                try:
                    trade_dates = get_trade_dates_since(start_date_str)
                    if len(trade_dates) <= 1:
                        log(f"  无新交易日，跳过")
                        skip_count += 1
                        continue
                    log(f"  待检查交易日: {len(trade_dates)} 个")
                except Exception as e:
                    log(f"  获取交易日历失败: {e}，尝试全量获取")
                    start_date_str = ''
            else:
                start_date_str = ''
                log(f"  无历史数据，全量获取")

            step_start = datetime.now()
            df, error = get_day_k_data(code, code_converted, start_date_str)

            if error:
                log(f"  获取失败: {error}")
                fail_count += 1
                continue

            if df is None or len(df) == 0:
                log(f"  未获取到数据")
                fail_count += 1
                continue

            step_start = datetime.now()
            save_count = insert_to_postgresql(df)

            if save_count > 0:
                log(f"  成功写入PostgreSQL: {save_count} 条")
                total_records += save_count
                success_count += 1
            else:
                log(f"  无新数据")
                skip_count += 1

            loop_elapsed = (datetime.now() - loop_start).total_seconds()
            log(f"  [循环总耗时] {loop_elapsed:.2f}秒")

        log("\n" + "=" * 50)
        log("K线数据抓取完成!")
        log(f"成功: {success_count} 个代码")
        log(f"失败: {fail_count} 个代码")
        log(f"跳过: {skip_count} 个代码")
        log(f"新增K线记录: {total_records} 条")
        log("=" * 50)
        
        update_sys_option('last_kline_data_fetch', log_func=log)

        try:
            tq.close()
        except:
            pass

        import json
        print("\n___JSON_OUTPUT_START___")
        print(json.dumps({
            "success": success_count,
            "fail": fail_count,
            "skip": skip_count,
            "records": total_records
        }))
        print("___JSON_OUTPUT_END___")

    except SystemExit:
        raise
    except KeyboardInterrupt:
        print_error("用户中断程序")
        try:
            tq.close()
        except:
            pass
        raise SystemExit(1)
    except Exception as e:
        error_details = traceback.format_exc()
        print_error(f"程序执行过程中发生未预期的错误\n{error_details}")
        try:
            tq.close()
        except:
            pass
        raise SystemExit(1)


if __name__ == "__main__":
    main()
