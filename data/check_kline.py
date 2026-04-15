import duckdb
import json
import sys
import os
from config import DB_PATH

try:
    # 获取命令行参数中的股票代码
    code = sys.argv[1] if len(sys.argv) > 1 else '600519'

    # 连接到DuckDB数据库
    con = duckdb.connect(DB_PATH)

    # 检查day_k_data表是否存在
    result = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='day_k_data';").fetchall()
    table_exists = len(result) > 0

    if not table_exists:
        # 如果表不存在，创建表
        con.execute('''
        CREATE TABLE IF NOT EXISTS day_k_data (
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
        ''')
        # 插入一些模拟数据
        con.execute('''
        INSERT INTO day_k_data (code, date, open, high, low, close, volume, amount)
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
        con.commit()

    # 查询K线数据
    result = con.execute('''
        SELECT code, date, open, high, low, close, volume, amount 
        FROM day_k_data 
        WHERE code = ? 
        ORDER BY date DESC
        LIMIT 50
    ''', [code]).fetchall()

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

    # 关闭连接
    con.close()
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
    import traceback
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)
