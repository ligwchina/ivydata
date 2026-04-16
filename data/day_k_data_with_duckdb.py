#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K线数据增量抓取程序（使用DuckDB临时存储，批量导入PostgreSQL）
"""

import os
import sys
import duckdb
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from datetime import datetime
import traceback

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../test/base'))
from data_num import get_trade_dates_since

tdx_install_path = r"D:\new_tdx64"
pyplugins_user_path = os.path.join(tdx_install_path, "PYPlugins", "user")
sys.path.insert(0, pyplugins_user_path)

from tqcenter import tq

DB_DIR = r'D:\dev\ai\ivydata\db'

POSTGRESQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'ivydata',
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF'
}


def get_db_connection():
    return psycopg2.connect(**POSTGRESQL_CONFIG)


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


def init_temp_db():
    """初始化临时DuckDB数据库"""
    db_path = os.path.join(DB_DIR, 'temp_ivy.duckdb')
    try:
        if os.path.exists(db_path):
            log(f"删除旧的临时数据库...")
            os.remove(db_path)
            wal_file = db_path + '.wal'
            if os.path.exists(wal_file):
                os.remove(wal_file)

        log(f"创建临时DuckDB数据库...")
        conn = duckdb.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE kline_data (
                id INTEGER PRIMARY KEY,
                code VARCHAR(20),
                date DATE,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume BIGINT,
                amount DOUBLE
            )
        """)

        conn.commit()
        return conn, db_path
    except Exception as e:
        print_error(f"初始化临时数据库失败\n详细信息: {e}")
        raise SystemExit(1)


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


def save_to_duckdb(duckdb_conn, df, id_counter):
    """保存数据到临时DuckDB"""
    try:
        if df is None or len(df) == 0:
            return 0, id_counter

        df['date'] = pd.to_datetime(df['date']).dt.date

        cursor = duckdb_conn.cursor()

        count = 0
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO kline_data (id, code, date, open, high, low, close, volume, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_counter,
                row['code'],
                row['date'],
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                int(row['volume']),
                row['amount']
            ))
            id_counter += 1
            count += 1

        return count, id_counter
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        return 0, id_counter


def transfer_to_postgresql(duckdb_conn, duckdb_path, start_time):
    """从DuckDB迁移数据到PostgreSQL"""
    full_start = datetime.now()
    try:
        log(f"\n开始从临时DuckDB迁移数据到PostgreSQL...")

        step_start = datetime.now()
        pg_conn = psycopg2.connect(**POSTGRESQL_CONFIG)
        log(f"  [PG连接] 耗时: {(datetime.now() - step_start).total_seconds():.2f}秒")

        pg_cursor = pg_conn.cursor()

        step_start = datetime.now()
        duckdb_cursor = duckdb_conn.cursor()
        duckdb_cursor.execute("SELECT * FROM kline_data ORDER BY id")
        kline_data_rows = duckdb_cursor.fetchall()
        log(f"  [DuckDB读取] 耗时: {(datetime.now() - step_start).total_seconds():.2f}秒, 读取到 {len(kline_data_rows)} 条")

        insert_data = []
        for row in kline_data_rows:
            insert_data.append((
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
                row[7],
                row[8]
            ))

        if insert_data:
            step_start = datetime.now()
            execute_values(pg_cursor, """
                INSERT INTO kline_data (code, date, open, high, low, close, volume, amount)
                VALUES %s
                ON CONFLICT (code, date) DO NOTHING
            """, insert_data)
            log(f"  [PG批量插入] 耗时: {(datetime.now() - step_start).total_seconds():.2f}秒")

            end_time = datetime.now()
            pg_cursor.execute("""
                INSERT INTO grab_record (type, status, start_time, end_time, message)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'kline_data',
                'completed',
                start_time,
                end_time,
                f'Successfully processed {len(insert_data)} K-line records'
            ))

            step_start = datetime.now()
            pg_conn.commit()
            log(f"  [PG提交] 耗时: {(datetime.now() - step_start).total_seconds():.2f}秒")
            log(f"成功迁移 {len(insert_data)} 条数据到PostgreSQL")

        pg_cursor.close()
        pg_conn.close()

        total_elapsed = (datetime.now() - full_start).total_seconds()
        log(f"  [迁移总耗时] {total_elapsed:.2f}秒")
        return len(insert_data)
    except Exception as e:
        print_error(f"迁移到PostgreSQL失败\n详细信息: {e}")
        raise SystemExit(1)


def delete_temp_db(duckdb_path):
    """删除临时DuckDB"""
    try:
        if os.path.exists(duckdb_path):
            log(f"删除临时DuckDB文件...")
            os.remove(duckdb_path)

            wal_file = duckdb_path + '.wal'
            if os.path.exists(wal_file):
                os.remove(wal_file)

            log(f"临时数据库已删除")
    except Exception as e:
        print_warning(f"删除临时数据库失败: {e}")


def main():
    log("=" * 50)
    log("K线数据增量抓取程序启动（DuckDB临时存储版）")
    log("=" * 50)

    start_time = datetime.now()

    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    try:
        tq.initialize(__file__)
        log("TQ数据接口初始化成功，使用路径: D:\\dev\\ai\\ivydata\\data\\day_k_data_with_duckdb.py")
    except Exception as e:
        log(f"TQ数据接口初始化失败: {e}")
        raise SystemExit(1)

    pg_conn = None
    duckdb_conn = None
    duckdb_path = None

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
        id_counter = 1

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

            if duckdb_conn is None:
                step_start = datetime.now()
                duckdb_conn, duckdb_path = init_temp_db()
                log(f"  [步骤2] 初始化DuckDB耗时: {(datetime.now() - step_start).total_seconds():.2f}秒")

            step_start = datetime.now()
            save_count, id_counter = save_to_duckdb(duckdb_conn, df, id_counter)
            log(f"  [步骤3] 写入DuckDB耗时: {(datetime.now() - step_start).total_seconds():.2f}秒")

            if save_count > 0:
                log(f"  成功写入临时DuckDB: {save_count} 条")
                total_records += save_count
                success_count += 1
            else:
                log(f"  无新数据")
                skip_count += 1

            loop_elapsed = (datetime.now() - loop_start).total_seconds()
            log(f"  [循环总耗时] {loop_elapsed:.2f}秒")

        if total_records > 0 and duckdb_conn:
            transfer_to_postgresql(duckdb_conn, duckdb_path, start_time)

        log("\n" + "=" * 50)
        log("K线数据抓取完成!")
        log(f"成功: {success_count} 个代码")
        log(f"失败: {fail_count} 个代码")
        log(f"跳过: {skip_count} 个代码")
        log(f"新增K线记录: {total_records} 条")
        log("=" * 50)

        if duckdb_conn:
            duckdb_conn.close()
            duckdb_conn = None

        if duckdb_path:
            delete_temp_db(duckdb_path)
            duckdb_path = None

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
        if duckdb_conn:
            try:
                duckdb_conn.close()
            except:
                pass
        if duckdb_path:
            delete_temp_db(duckdb_path)
        try:
            tq.close()
        except:
            pass
        raise SystemExit(1)
    except Exception as e:
        error_details = traceback.format_exc()
        print_error(f"程序执行过程中发生未预期的错误\n{error_details}")
        log(f"\n已处理成功的数据已保存到数据库")
        log(f"未处理成功的代码可在下次运行时重新处理")
        if duckdb_conn:
            try:
                duckdb_conn.close()
            except:
                pass
        if duckdb_path:
            delete_temp_db(duckdb_path)
        try:
            tq.close()
        except:
            pass
        raise SystemExit(1)


if __name__ == "__main__":
    main()
