import duckdb
import json

# 连接到DuckDB数据库
con = duckdb.connect('stock_data.duckdb')

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

# 输出JSON
print(json.dumps(base_data, ensure_ascii=False))

# 关闭连接
con.close()
