import os
import sys
import duckdb
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

DB_PATH = r'D:\dev\ai\ivydata\db\ivy.duckdb'
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
        conn = duckdb.connect(DB_PATH)
    except Exception as e:
        print_error(f"无法连接数据库: {DB_PATH}\n详细信息: {e}")
        raise SystemExit(1)

    try:
        create_day_k_sql = """
        CREATE TABLE IF NOT EXISTS t_day_k (
            code VARCHAR,
            date DATE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume DOUBLE,
            amount DOUBLE,
            PRIMARY KEY (code, date)
        )
        """
        conn.execute(create_day_k_sql)

        create_grab_record_sql = """
        CREATE TABLE IF NOT EXISTS t_grab_record (
            code VARCHAR PRIMARY KEY,
            start_time TIMESTAMP,
            end_time TIMESTAMP
        )
        """
        conn.execute(create_grab_record_sql)

        log("数据库表初始化完成")
        return conn
    except Exception as e:
        print_error(f"初始化数据库表失败\n详细信息: {e}")
        conn.close()
        raise SystemExit(1)


def get_codes_to_grab(conn):
    """获取需要抓取K线数据的代码列表"""
    try:
        sql = """
        SELECT b.code, b.code_converted
        FROM t_base b
        LEFT JOIN t_grab_record g ON b.code = g.code
        WHERE g.code IS NULL
        ORDER BY b.stock_or_fund, b.code
        """
        result = conn.execute(sql).fetchall()
        return result
    except Exception as e:
        print_error(f"查询待抓取代码列表失败\n详细信息: {e}")
        raise SystemExit(1)


def get_day_k_data(stock_code, stock_code_full):
    """从通达信获取日K线数据"""
    try:
        raw_data = tq.get_market_data(
            field_list=[],
            stock_list=[stock_code_full],
            start_time='',
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


def save_day_k_data(conn, df, code):
    """保存K线数据到数据库"""
    if df is None or len(df) == 0:
        return 0, None

    try:
        conn.execute(f"DELETE FROM t_day_k WHERE code = '{code}'")

        conn.register('k_data', df)
        conn.execute("""
            INSERT INTO t_day_k (code, date, open, high, low, close, volume, amount)
            SELECT code, date, open, high, low, close, volume, amount FROM k_data
        """)
        conn.unregister('k_data')

        count = len(df)
        return count, None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        return 0, error_msg


def update_grab_record(conn, code, start_time, end_time):
    """更新抓取记录"""
    try:
        conn.execute("""
            INSERT OR REPLACE INTO t_grab_record (code, start_time, end_time)
            VALUES (?, ?, ?)
        """, [code, start_time, end_time])
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
    log("K线数据抓取程序启动")
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

        codes = get_codes_to_grab(conn)
        log(f"需要抓取的代码数量: {len(codes)}")

        if not codes:
            log("\n没有需要抓取的代码")
            conn.close()
            tq.close()
            log("程序正常退出")
            return

        log("\n" + "=" * 50)
        log("开始抓取数据...")
        log("=" * 50)

        success_count = 0
        fail_count = 0

        for i, (code, code_converted) in enumerate(codes):
            if is_run == 0 and i > 0:
                log(f"\n配置 is_run=0，抓取单个代码后停止")
                break

            log(f"\n[{i+1}/{len(codes)}] 正在抓取: {code} ({code_converted})")

            start_time = datetime.now()

            df, error = get_day_k_data(code, code_converted)

            if error and "初始化失败" in str(error):
                log(f"  TQ接口失效，尝试重新初始化...")
                try:
                    tq.close()
                except:
                    pass
                try:
                    tq.initialize(__file__)
                    log(f"  TQ重新初始化成功")
                    df, error = get_day_k_data(code, code_converted)
                except Exception as reinit_error:
                    log(f"  TQ重新初始化失败: {reinit_error}")

            if error:
                fail_count += 1
                log(f"  获取数据失败: {error}")
                log(f"  该代码未抓取成功，不记录抓取记录")
                log(f"  将在下次运行时重新尝试抓取")
                continue

            if df is None or len(df) == 0:
                fail_count += 1
                log(f"  未获取到数据")
                log(f"  该代码未抓取成功，不记录抓取记录")
                continue

            save_count, save_error = save_day_k_data(conn, df, code)

            if save_error:
                fail_count += 1
                log(f"  保存数据失败: {save_error}")
                log(f"  数据未保存，不记录抓取记录")
                log(f"  将在下次运行时重新尝试")
                continue

            record_error = update_grab_record(conn, code, start_time, datetime.now())
            if record_error:
                log_warning(f"更新抓取记录失败: {record_error}")

            success_count += 1
            log(f"  成功插入{save_count}条数据")
            log(f"  抓取完成: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        log("\n" + "=" * 50)
        log("抓取任务完成!")
        log(f"成功: {success_count} 个代码")
        log(f"失败: {fail_count} 个代码")
        log("=" * 50)

    except SystemExit:
        raise
    except KeyboardInterrupt:
        graceful_exit(conn, "用户中断程序")
    except Exception as e:
        error_details = traceback.format_exc()
        print_error(f"程序执行过程中发生未预期的错误\n{error_details}")
        log(f"\n已抓取成功的数据已保存到数据库")
        log(f"未抓取成功的代码可在下次运行时重新抓取")
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
