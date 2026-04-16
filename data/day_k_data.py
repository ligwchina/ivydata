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


def ensure_log_dir():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def log(message, end='\n'):
    print(message, end=end)
    ensure_log_dir()
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', f'grab_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + end)


def print_error(message):
    log(f"\n{'='*50}")
    log(f"错误: {message}")
    log(f"{'='*50}\n")


def print_warning(message):
    log(f"\n警告: {message}\n")


def get_config_value():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.txt')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('is_run='):
                    return int(line.split('=')[1])
    except FileNotFoundError:
        print_warning(f"配置文件不存在: {config_path}，将使用默认值 is_run=0")
    except Exception as e:
        print_warning(f"读取配置文件失败: {e}，将使用默认值 is_run=0")
    return 0


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kline_data (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            open NUMERIC(18, 4) NOT NULL,
            high NUMERIC(18, 4) NOT NULL,
            low NUMERIC(18, 4) NOT NULL,
            close NUMERIC(18, 4) NOT NULL,
            volume BIGINT NOT NULL,
            amount NUMERIC(18, 4) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code, date)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grab_record (
            code VARCHAR(20) PRIMARY KEY,
            start_time TIMESTAMP,
            end_time TIMESTAMP
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kline_code ON kline_data(code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kline_date ON kline_data(date)")
    
    conn.commit()
    log("数据库表初始化完成")
    return conn


def get_all_codes(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, code_converted FROM base_data ORDER BY stock_or_fund, code
        """)
        result = cursor.fetchall()
        
        cursor.execute("SELECT code FROM grab_record")
        grabbed_codes = {row[0] for row in cursor.fetchall()}
        
        codes = []
        for row in result:
            code, code_converted = row
            codes.append({
                'code': code,
                'code_converted': code_converted,
                'is_new': code not in grabbed_codes
            })
        
        return codes
    except Exception as e:
        print_error(f"查询代码列表失败\n详细信息: {e}")
        raise SystemExit(1)


def get_day_k_data(stock_code, stock_code_full, start_date=''):
    try:
        raw_data = tq.get_market_data(
            field_list=[],
            stock_list=[stock_code_full],
            start_time=start_date,
            end_time='',
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


def save_day_k_data(conn, df, code, incremental=True):
    if df is None or len(df) == 0:
        return 0, None

    try:
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        cursor = conn.cursor()
        
        if incremental:
            cursor.execute("SELECT date FROM kline_data WHERE code = %s", (code,))
            existing_dates = {row[0] for row in cursor.fetchall()}
            new_df = df[~df['date'].isin(existing_dates)]
        else:
            cursor.execute("DELETE FROM kline_data WHERE code = %s", (code,))
            new_df = df

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


def get_last_k_date(conn, code):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(date) FROM kline_data WHERE code = %s", (code,))
        result = cursor.fetchone()
        if result and result[0]:
            return str(result[0])
        return None
    except Exception as e:
        return None


def update_grab_record(conn, code, start_time, end_time):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO grab_record (code, start_time, end_time)
            VALUES (%s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                start_time = EXCLUDED.start_time,
                end_time = EXCLUDED.end_time
        """, (code, start_time, end_time))
        conn.commit()
        return None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        return error_msg


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


def main():
    log("=" * 50)
    log("K线数据增量抓取程序启动")
    log("=" * 50)
    
    try:
        tq.initialize(__file__)
        log("TQ数据接口初始化成功")
    except Exception as e:
        log(f"TQ数据接口初始化失败: {e}")
        raise SystemExit(1)

    conn = None

    try:
        conn = init_db()

        is_run = get_config_value()
        log(f"配置 is_run = {is_run}")

        codes = get_all_codes(conn)
        new_codes = [c for c in codes if c['is_new']]
        existing_codes = [c for c in codes if not c['is_new']]
        
        log(f"总代码数量: {len(codes)}")
        log(f"  新代码（待首次抓取）: {len(new_codes)}")
        log(f"  已有代码（待增量更新）: {len(existing_codes)}")

        if not codes:
            log("\n没有代码需要处理")
            conn.close()
            tq.close()
            log("程序正常退出")
            return

        log("\n" + "=" * 50)
        log("开始处理数据...")
        log("=" * 50)

        success_count = 0
        fail_count = 0
        total_new_records = 0

        for i, code_info in enumerate(codes):
            if is_run == 0 and i > 0:
                log(f"\n配置 is_run=0，处理单个代码后停止")
                break

            code = code_info['code']
            code_converted = code_info['code_converted']
            is_new = code_info['is_new']

            status = "首次抓取" if is_new else "增量更新"
            log(f"\n[{i+1}/{len(codes)}] 正在{status}: {code} ({code_converted})")

            start_time = datetime.now()

            start_date = ''
            last_date = ''
            if not is_new:
                last_date = get_last_k_date(conn, code)
                if last_date:
                    next_date = pd.to_datetime(last_date) + pd.Timedelta(days=1)
                    start_date = str(next_date).replace('-', '')
                    log(f"  上次抓取截止日期: {last_date}，从 {next_date} 开始增量获取")
            
            df, error = get_day_k_data(code, code_converted, start_date)

            if error and "初始化失败" in str(error):
                log(f"  TQ接口失效，尝试重新初始化...")
                try:
                    tq.close()
                except:
                    pass
                try:
                    tq.initialize(__file__)
                    log(f"  TQ重新初始化成功")
                    df, error = get_day_k_data(code, code_converted, start_date)
                except Exception as reinit_error:
                    log(f"  TQ重新初始化失败: {reinit_error}")

            if error:
                fail_count += 1
                log(f"  获取数据失败: {error}")
                if is_new:
                    log(f"  该代码未抓取成功，不记录抓取记录")
                    log(f"  将在下次运行时重新尝试抓取")
                continue

            if df is None or len(df) == 0:
                if is_new:
                    fail_count += 1
                    log(f"  未获取到数据")
                    log(f"  该代码未抓取成功，不记录抓取记录")
                else:
                    log(f"  没有新数据")
                    success_count += 1
                continue

            if not is_new and start_date:
                try:
                    start_date_str = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
                    expected_dates = get_trade_dates_since(start_date_str)
                    expected_count = len(expected_dates)
                    actual_count = len(df)
                    
                    log(f"  验证数据完整性: 预期 {expected_count} 个交易日，实际获取 {actual_count} 条数据")
                    
                    if actual_count != expected_count:
                        log(f"  数据不完整！预期 {expected_count} 条，实际 {actual_count} 条")
                        log(f"  请检查通达信本地数据是否完整")
                        graceful_exit(conn, f"数据完整性验证失败: {code} 缺少数据")
                    else:
                        log(f"  数据完整性验证通过")
                except Exception as e:
                    log(f"  数据完整性验证失败: {e}")
                    graceful_exit(conn, f"数据完整性验证异常: {e}")

            save_count, save_error = save_day_k_data(conn, df, code, incremental=True)

            if save_error:
                fail_count += 1
                log(f"  保存数据失败: {save_error}")
                if is_new:
                    log(f"  数据未保存，不记录抓取记录")
                    log(f"  将在下次运行时重新尝试")
                continue

            record_error = update_grab_record(conn, code, start_time, datetime.now())
            if record_error:
                print_warning(f"更新抓取记录失败: {record_error}")

            success_count += 1
            total_new_records += save_count
            if save_count > 0:
                log(f"  成功插入{save_count}条新数据")
            log(f"  处理完成: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        log("\n" + "=" * 50)
        log("抓取任务完成!")
        log(f"成功: {success_count} 个代码")
        log(f"失败: {fail_count} 个代码")
        log(f"新增K线记录: {total_new_records} 条")
        log("=" * 50)

        import json
        print("\n___JSON_OUTPUT_START___")
        print(json.dumps({"success": success_count, "fail": fail_count, "records": total_new_records}))
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
    main()
