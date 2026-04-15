import duckdb
import json
import sys
import os
from config import DB_PATH

try:
    # 连接到DuckDB数据库
    con = duckdb.connect(DB_PATH)

    # 检查t_base表是否存在
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='t_base';")
    table_exists = cursor.fetchone()

    if not table_exists:
        # 如果表不存在，创建表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS t_base (
            code VARCHAR PRIMARY KEY,
            name VARCHAR,
            code_converted VARCHAR,
            exchange VARCHAR,
            stock_or_fund INTEGER
        )
        ''')
        # 插入一些模拟数据
        insert_query = '''
        INSERT INTO t_base (code, name, code_converted, exchange, stock_or_fund)
        VALUES 
        ('600519', '贵州茅台', '600519.SH', 'SH', 1),
        ('000858', '五粮液', '000858.SZ', 'SZ', 1),
        ('000001', '平安银行', '000001.SZ', 'SZ', 1),
        ('000002', '万科A', '000002.SZ', 'SZ', 1),
        ('510300', '沪深300ETF', '510300.SH', 'SH', 2),
        ('159915', '创业板ETF', '159915.SZ', 'SZ', 2)
        '''
        cursor.execute(insert_query)
        con.commit()

    # 查询基础数据
    cursor.execute('''
        SELECT code, name, code_converted, exchange, stock_or_fund 
        FROM t_base 
        ORDER BY stock_or_fund, code
    ''')
    result = cursor.fetchall()

    # 转换为JSON格式
    base_data = []
    for row in result:
        base_data.append({
            'code': row[0],
            'name': row[1],
            'code_converted': row[2],
            'exchange': row[3],
            'stock_or_fund': row[4]
        })

    # 输出JSON，确保正确编码
    import sys
    if sys.version_info >= (3, 7):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(base_data, ensure_ascii=False))

    # 关闭连接
    con.close()
except Exception as e:
    print(f"Error: {str(e)}", file=sys.stderr)
    import traceback
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)
