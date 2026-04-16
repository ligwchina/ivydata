#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并补充K线数据脚本
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

# PostgreSQL 配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'ivydata',
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_database():
    """检查并初始化数据库表"""
    try:
        log("检查数据库表结构...")
        
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
            log("错误: base_data 表不存在，请先运行 base_data.py 创建基础数据")
            pg_cursor.close()
            pg_conn.close()
            raise SystemExit(1)
        
        pg_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'kline_data'
            )
        """)
        kline_data_exists = pg_cursor.fetchone()[0]
        
        if not kline_data_exists:
            log("错误: kline_data 表不存在，请先运行 day_k_data.py 创建K线数据表")
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
        print_error(f"检查数据库失败\n详细信息: {e}")
        raise SystemExit(1)


def ensure_log_dir():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def log(message, end='\n'):
    print(message, end=end)
    ensure_log_dir()
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', f'check_fill_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + end)


def print_error(message):
    log(f"\n{'='*50}")
    log(f"错误: {message}")
    log(f"{'='*50}\n")


def print_warning(message):
    log(f"\n警告: {message}\n")


def get_all_codes_with_kline(conn, target_code=None):
    """获取所有有K线数据的代码"""
    try:
        cursor = conn.cursor()
        
        if target_code:
            cursor.execute("""
                SELECT DISTINCT code FROM kline_data WHERE code = %s ORDER BY code
            """, (target_code,))
        else:
            cursor.execute("""
                SELECT DISTINCT code FROM kline_data ORDER BY code
            """)
        
        result = cursor.fetchall()
        return [row[0] for row in result]
    except Exception as e:
        print_error(f"查询代码列表失败\n详细信息: {e}")
        raise SystemExit(1)


def get_code_info(conn, code):
    """获取代码的基本信息"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code_converted FROM base_data WHERE code = %s
        """, (code,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print_error(f"查询代码信息失败\n详细信息: {e}")
        return None


def get_existing_dates(conn, code):
    """获取代码已有的K线日期"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date FROM kline_data WHERE code = %s ORDER BY date
        """, (code,))
        result = cursor.fetchall()
        return [row[0] for row in result]
    except Exception as e:
        print_error(f"查询已有日期失败\n详细信息: {e}")
        return []


def get_date_range(conn, code):
    """获取代码的日期范围"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MIN(date) as min_date, MAX(date) as max_date FROM kline_data WHERE code = %s
        """, (code,))
        result = cursor.fetchone()
        return result[0], result[1]
    except Exception as e:
        print_error(f"查询日期范围失败\n详细信息: {e}")
        return None, None


def get_day_k_data(stock_code, stock_code_full, start_date='', end_date=''):
    """获取K线数据"""
    try:
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
        return df, None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        return None, error_msg


def save_kline_data(conn, df, code):
    """保存K线数据"""
    if df is None or len(df) == 0:
        return 0, None

    try:
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        cursor = conn.cursor()
        
        # 获取已有日期
        cursor.execute("SELECT date FROM kline_data WHERE code = %s", (code,))
        existing_dates = {row[0] for row in cursor.fetchall()}
        
        # 只插入新数据
        new_df = df[~df['date'].isin(existing_dates)]
        
        count = 0
        
        if len(new_df) > 0:
            insert_data = []
            for _, row in new_df.iterrows():
                insert_data.append((
                    row['code'],
                    row['date'],
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume'],
                    row['amount']
                ))
            
            execute_values(cursor, """
                INSERT INTO kline_data (code, date, open, high, low, close, volume, amount)
                VALUES %s
                ON CONFLICT (code, date) DO NOTHING
            """, insert_data)
            count = len(new_df)

        conn.commit()
        return count, None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        return 0, error_msg


def graceful_exit(conn, message):
    print_error(message)
    if conn:
        try:
            conn.close()
        except:
            pass
    try:
        tq.close()
    except:
        pass
    raise SystemExit(1)


def main(target_code=None):
    log("=" * 50)
    log("K线数据检查并补充程序启动")
    log("=" * 50)
    
    init_database()
    
    try:
        tq.initialize(__file__)
        log("TQ数据接口初始化成功")
    except Exception as e:
        log(f"TQ数据接口初始化失败: {e}")
        raise SystemExit(1)

    conn = None

    try:
        conn = get_db_connection()

        codes = get_all_codes_with_kline(conn, target_code)
        
        log(f"\n总代码数量: {len(codes)}")

        if not codes:
            log("\n没有代码需要处理")
            conn.close()
            tq.close()
            log("程序正常退出")
            return

        log("\n" + "=" * 50)
        log("开始检查并补充数据...")
        log("=" * 50)

        success_count = 0
        fail_count = 0
        total_new_records = 0
        codes_with_missing = []

        for i, code in enumerate(codes):
            log(f"\n[{i+1}/{len(codes)}] 正在检查: {code}")

            code_converted = get_code_info(conn, code)
            if not code_converted:
                log(f"  找不到代码的转换信息，跳过")
                fail_count += 1
                continue

            min_date, max_date = get_date_range(conn, code)
            if not min_date or not max_date:
                log(f"  找不到日期范围，跳过")
                fail_count += 1
                continue

            log(f"  日期范围: {min_date} 到 {max_date}")

            # 获取交易日历
            try:
                trade_dates = get_trade_dates_since(str(min_date))
                # 筛选到 max_date
                trade_dates = trade_dates[trade_dates <= pd.to_datetime(max_date)]
                log(f"  交易日数量: {len(trade_dates)}")
            except Exception as e:
                log(f"  获取交易日历失败: {e}")
                fail_count += 1
                continue

            # 获取已有日期
            existing_dates = get_existing_dates(conn, code)
            log(f"  已有K线数量: {len(existing_dates)}")

            # 找出缺失的日期
            existing_date_set = set(existing_dates)
            trade_date_set = set(trade_dates.dt.date)
            missing_dates = sorted(trade_date_set - existing_date_set)
            
            if missing_dates:
                log(f"  [WARNING] 发现 {len(missing_dates)} 个缺失日期")
                codes_with_missing.append({
                    'code': code,
                    'code_converted': code_converted,
                    'missing_count': len(missing_dates),
                    'missing_dates': missing_dates[:10]  # 只显示前10个
                })
                
                # 补充缺失数据
                log(f"  开始补充缺失数据...")
                
                # 从最早缺失日期开始获取
                start_date_str = missing_dates[0].strftime('%Y%m%d')
                end_date_str = missing_dates[-1].strftime('%Y%m%d')
                
                df, error = get_day_k_data(code, code_converted, start_date_str, end_date_str)
                
                if error:
                    log(f"  获取数据失败: {error}")
                    fail_count += 1
                    continue
                
                if df is None or len(df) == 0:
                    log(f"  未获取到数据")
                    fail_count += 1
                    continue
                
                save_count, save_error = save_kline_data(conn, df, code)
                
                if save_error:
                    log(f"  保存数据失败: {save_error}")
                    fail_count += 1
                    continue
                
                success_count += 1
                total_new_records += save_count
                if save_count > 0:
                    log(f"  成功补充 {save_count} 条新数据")
            else:
                log(f"  [OK] 数据完整，没有缺失")
                success_count += 1

        log("\n" + "=" * 50)
        log("检查并补充任务完成!")
        log(f"成功: {success_count} 个代码")
        log(f"失败: {fail_count} 个代码")
        log(f"新增K线记录: {total_new_records} 条")
        
        if codes_with_missing:
            log(f"\n有缺失数据的代码 ({len(codes_with_missing)}):")
            for item in codes_with_missing:
                log(f"  {item['code']}: {item['missing_count']} 个缺失日期")
                if item['missing_dates']:
                    log(f"    示例: {', '.join(str(d) for d in item['missing_dates'])}")
        
        log("=" * 50)

        import json
        print("\n___JSON_OUTPUT_START___")
        print(json.dumps({
            "success": success_count, 
            "fail": fail_count, 
            "records": total_new_records,
            "codes_with_missing": codes_with_missing
        }))
        print("___JSON_OUTPUT_END___")

    except SystemExit:
        raise
    except KeyboardInterrupt:
        graceful_exit(conn, "用户中断程序")
    except Exception as e:
        error_details = traceback.format_exc()
        print_error(f"程序执行过程中发生未预期的错误\n{error_details}")
        log(f"\n已处理成功的数据已保存到数据库")
        log(f"未处理成功的代码可在下次运行时重新处理")
        if conn:
            conn.close()
        try:
            tq.close()
        except:
            pass
        raise SystemExit(1)
    else:
        if conn:
            conn.close()
        try:
            tq.close()
        except:
            pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='检查并补充K线数据')
    parser.add_argument('--code', type=str, help='指定代码检查（默认检查所有代码）')
    args = parser.parse_args()
    
    main(target_code=args.code)
