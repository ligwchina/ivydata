import duckdb

# 连接到数据库
DB_PATH = r'D:\dev\ai\ivydata\db\ivy.duckdb'

print(f'连接到数据库: {DB_PATH}')
conn = duckdb.connect(DB_PATH)

# 检查表是否存在
print('\n检查数据库中的表:')
tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
print(f'表列表: {tables}')

# 检查表结构
print('\n检查base_data表结构:')
columns = conn.execute('PRAGMA table_info(base_data)').fetchall()
for column in columns:
    print(f'列名: {column[1]}, 类型: {column[2]}, 非空: {column[3]}, 默认值: {column[4]}, 主键: {column[5]}')

# 检查数据行数
print('\n检查base_data表中的数据行数:')
count = conn.execute('SELECT COUNT(*) as count FROM base_data').fetchone()
print(f'数据行数: {count[0]}')

# 查看前10条数据
print('\n查看前10条数据:')
rows = conn.execute('SELECT * FROM base_data LIMIT 10').fetchall()
for row in rows:
    print(row)

# 关闭连接
conn.close()
print('\n连接已关闭')
