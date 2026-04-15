import duckdb
import json
import sys
import os

try:
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 数据库文件路径
    db_path = os.path.join(script_dir, '..', 'stock_data.duckdb')
    
    # 连接到DuckDB数据库
    con = duckdb.connect(db_path)

    # 检查base_data表是否存在
    table_exists = con.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'base_data';").fetchone()

    if not table_exists:
        # 如果表不存在，创建表
        con.execute('''
        CREATE TABLE IF NOT EXISTS base_data (
            code VARCHAR,
            name VARCHAR,
            code_converted VARCHAR,
            exchange VARCHAR,
            stock_or_fund VARCHAR,
            PRIMARY KEY (code)
        )
        ''')
        # 插入一些模拟数据
        con.execute('''
        INSERT INTO base_data (code, name, code_converted, exchange, stock_or_fund)
        VALUES 
        ('600519', '贵州茅台', 'sh600519', 'SH', 'stock'),
        ('000858', '五粮液', 'sz000858', 'SZ', 'stock'),
        ('000001', '平安银行', 'sz000001', 'SZ', 'stock'),
        ('000002', '万科A', 'sz000002', 'SZ', 'stock'),
        ('510300', '沪深300ETF', 'sh510300', 'SH', 'fund'),
        ('159915', '创业板ETF', 'sz159915', 'SZ', 'fund')
        ''')

    # 查询基础数据
    result = con.execute('''
        SELECT code, name, code_converted, exchange, stock_or_fund 
        FROM base_data 
        ORDER BY stock_or_fund, code
    ''').fetchall()

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
