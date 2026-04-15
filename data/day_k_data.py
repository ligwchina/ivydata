import os
import sys
import psycopg2
import pandas as pd
from datetime import datetime
import traceback

# 1. 定义通达信安装根目录
tdx_install_path = r"D:\new_tdx64"  # 请修改为你自己的通达信路径

# 2. 拼接出 PYPlugins/user 的绝对路径
pyplugins_user_path = os.path.join(tdx_install_path, "PYPlugins", "user")

# 3. 将该路径插入到 sys.path 的第一位，确保优先加载
sys.path.insert(0, pyplugins_user_path)

# 4. 现在可以愉快地导入了
from tqcenter import tq

from config import DB_CONNECTION_STRING
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.txt')
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
LOG_FILE = os.path.join(LOG_DIR, f'grab_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')


def ensure_log_dir():
    """确保日志目录存在"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


def log(message, end='\n'):
    """输出日志到控制台和日志文件"""
    print(message, end=end)
    ensure_log_dir()
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(message + end)


def print_error(message):
    """打印错误信息"""
    log(f"\n{'='*50}")
    log(f"错误: {message}")
    log(f"{'='*50}\n")


def print_warning(message):
    """打印警告信息"""
    log(f"\n警告: {message}\n")


def get_config_value():
    """读取配置文件中的is_run值"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('is_run='):
                    return int(line.split('=')[1])
    except FileNotFoundError:
        print_warning(f"配置文件不存在: {CONFIG_PATH}，将使用默认值 is_run=0")
    except Exception as e:
        print_warning(f"读取配置文件失败: {e}，将使用默认值 is_run=0")
    return 0


def init_db():
    """初始化数据库和表"""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
    except Exception as e:
        print_error(f"无法连接数据库: {DB_CONNECTION_STRING}\n详细信息: {e}")
        raise SystemExit(1)

    try:
        create_day_k_sql = """
        CREATE TABLE IF NOT EXISTS t_day_k (
            code VARCHAR,
            date DATE,
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,
            amount DOUBLE PRECISION,
            PRIMARY KEY (code, date)
        )
        """
        cursor.execute(create_day_k_sql)

        create_grab_record_sql = """
        CREATE TABLE IF NOT EXISTS t_grab_record (
            code VARCHAR PRIMARY KEY,
            start_time TIMESTAMP,
            end_time TIMESTAMP
        )
        """
        cursor.execute(create_grab_record_sql)

        conn.commit()
        cursor.close()
        log("数据库表初始化完成")
        return conn
    except Exception as e:
        print_error(f"初始化数据库表失败\n详细信息: {e}")
        cursor.close()
        conn.close()
        raise SystemExit(1)


def get_all_codes(conn):
    """获取所有代码列表，包括需要首次抓取和需要增量更新的代码"""
    try:
        cursor = conn.cursor()
        sql = """
        SELECT b.code, b.code_converted, g.code as grabbed
        FROM t_base b
        LEFT JOIN t_grab_record g ON b.code = g.code
        ORDER BY b.stock_or_fund, b.code
        """
        cursor.execute(sql)
        result = cursor.fetchall()
        codes = []
        for row in result:
            code, code_converted, grabbed = row
            codes.append({
                'code': code,
                'code_converted': code_converted,
                'is_new': grabbed is None
            })
        cursor.close()
        return codes
    except Exception as e:
        print_error(f"查询代码列表失败\n详细信息: {e}")
        raise SystemExit(1)


def get_day_k_data(stock_code, stock_code_full, start_date=''):
    """从通达信获取日K线数据
    start_date: 开始日期，格式为YYYY-MM-DD，为空表示获取全部历史数据
    """
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
    """保存K线数据到数据库
    incremental: True表示增量模式，只插入新数据；False表示全量替换
    """
    if df is None or len(df) == 0:
        return 0, None

    try:
        cursor = conn.cursor()
        if incremental:
            # 获取已有的日期
            existing_dates = set()
            cursor.execute("SELECT date FROM t_day_k WHERE code = %s", (code,))
            result = cursor.fetchall()
            for row in result:
                existing_dates.add(row[0])

            # 只保留新数据
            df['date'] = pd.to_datetime(df['date']).dt.date
            new_df = df[~df['date'].isin(existing_dates)]
            
            if len(new_df) > 0:
                insert_query = """
                    INSERT INTO t_day_k (code, date, open, high, low, close, volume, amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                data = new_df[['code', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount']].values.tolist()
                cursor.executemany(insert_query, data)
                conn.commit()
            count = len(new_df)
        else:
            # 全量替换模式
            cursor.execute("DELETE FROM t_day_k WHERE code = %s", (code,))
            insert_query = """
                INSERT INTO t_day_k (code, date, open, high, low, close, volume, amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            data = df[['code', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount']].values.tolist()
            cursor.executemany(insert_query, data)
            conn.commit()
            count = len(df)
        cursor.close()
        return count, None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        return 0, error_msg


def get_last_k_date(conn, code):
    """获取某个代码的最后一条K线数据日期
    返回: 日期字符串格式YYYY-MM-DD，如果没有数据则返回None
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(date) FROM t_day_k WHERE code = %s", (code,))
        result = cursor.fetchone()
        cursor.close()
        if result and result[0]:
            return str(result[0])
        return None
    except Exception as e:
        return None


def update_grab_record(conn, code, start_time, end_time):
    """更新抓取记录"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO t_grab_record (code, start_time, end_time)
            VALUES (%s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time
        """, (code, start_time, end_time))
        conn.commit()
        cursor.close()
        return None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        return error_msg


def graceful_exit(conn, message):
    """优雅退出程序"""
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
    """主函数"""
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

            # 确定开始日期，通达信要求格式为YYYYMMDD
            start_date = ''
            last_date = ''
            if not is_new:
                # 获取最后日期并加一天
                result = conn.execute(f"SELECT MAX(date) FROM t_day_k WHERE code = '{code}'").fetchone()
                if result and result[0]:
                    last_date = result[0]
                    # 加一天作为开始日期
                    next_date = last_date + pd.Timedelta(days=1)
                    # 转换为YYYYMMDD格式
                    start_date = str(next_date).replace('-', '')
                    log(f"  上次抓取截止日期: {last_date}，从 {next_date} 开始增量获取")
            
            # 使用通达信接口的日期过滤功能
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

            # 增量保存数据
            save_count, save_error = save_day_k_data(conn, df, code, incremental=True)

            if save_error:
                fail_count += 1
                log(f"  保存数据失败: {save_error}")
                if is_new:
                    log(f"  数据未保存，不记录抓取记录")
                    log(f"  将在下次运行时重新尝试")
                continue

            # 无论是否是新代码，都更新抓取记录
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
