import duckdb
import json
import sys

# 获取命令行参数中的股票代码
code = sys.argv[1] if len(sys.argv) > 1 else '600519'

# 连接到DuckDB数据库
con = duckdb.connect('stock_data.duckdb')

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
        'date': row[1],
        'open': float(row[2]),
        'high': float(row[3]),
        'low': float(row[4]),
        'close': float(row[5]),
        'volume': int(row[6]),
        'amount': float(row[7])
    })

# 输出JSON
print(json.dumps(kline_data, ensure_ascii=False))

# 关闭连接
con.close()
