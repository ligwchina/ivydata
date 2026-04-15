import psycopg2
import json
import sys
import os
from config import DB_CONNECTION_STRING

try:
    # 获取命令行参数中的股票代码
    code = sys.argv[1] if len(sys.argv) > 1 else '600519'

    # 连接到PostgreSQL数据库
    con = psycopg2.connect(DB_CONNECTION_STRING)

    # 检查t_day_k表是否存在
    cursor = con.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 't_day_k';")
    table_exists = cursor.fetchone()

    if not table_exists:
        # 如果表不存在，创建表
        cursor.execute('''
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
        ''')
        # 插入一些模拟数据
        insert_query = '''
        INSERT INTO t_day_k (code, date, open, high, low, close, volume, amount)
        VALUES 
        ('600519', '2026-04-14', 1800, 1820, 1790, 1810, 1000000, 1810000000),
        ('600519', '2026-04-13', 1780, 1800, 1770, 1790, 900000, 1611000000),
        ('600519', '2026-04-12', 1760, 1780, 1750, 1780, 800000, 1424000000),
        ('600519', '2026-04-11', 1740, 1760, 1730, 1760, 700000, 1232000000),
        ('600519', '2026-04-10', 1720, 1740, 1710, 1740, 600000, 1044000000),
        ('000858', '2026-04-14', 160, 162, 159, 161, 2000000, 322000000),
        ('000858', '2026-04-13', 158, 160, 157, 159, 1800000, 286200000),
        ('000858', '2026-04-12', 156, 158, 155, 158, 1600000, 2528000000),
        ('000858', '2026-04-11', 154, 156, 153, 156, 1400000, 2184000000),
        ('000858', '2026-04-10', 152, 154, 151, 154, 1200000, 1848000000)
        ''')
        cursor.execute(insert_query)
        con.commit()

    # 查询K线数据
    cursor.execute('''
        SELECT code, date, open, high, low, close, volume, amount 
        FROM t_day_k 
        WHERE code = %s 
        ORDER BY date DESC
        LIMIT 50
    ''', (code,))
    result = cursor.fetchall()

    # 转换为JSON格式
    kline_data = []
    for row in result:
        kline_data.append({
            'code': row[0],
            'date': str(row[1]),
            'open': float(row[2]),
            'high': float(row[3]),
            'low': float(row[4]),
            'close': float(row[5]),
            'volume': int(row[6]),
            'amount': float(row[7])
        })

    # 输出JSON，确保正确编码
    import sys
    if sys.version_info >= (3, 7):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(kline_data, ensure_ascii=False))

    # 关闭游标和连接
    cursor.close()
    con.close()
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
    import traceback
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)
