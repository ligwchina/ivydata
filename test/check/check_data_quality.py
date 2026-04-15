import psycopg2
import akshare as ak
import sys

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF',
    'database': 'ivydata'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def check_data_quality():
    conn = get_db_connection()
    cur = conn.cursor()

    print("=" * 60)
    print("数据质量检查报告")
    print("=" * 60)

    # 1. 检查数据总量
    cur.execute("SELECT COUNT(*) FROM base_data")
    total_count = cur.fetchone()[0]
    print(f"\n1. 数据总量: {total_count} 条")

    # 2. 检查重复数据
    cur.execute("""
        SELECT code, COUNT(*) as cnt 
        FROM base_data 
        GROUP BY code 
        HAVING COUNT(*) > 1
    """)
    duplicates = cur.fetchall()
    if duplicates:
        print(f"\n2. 发现重复数据 ({len(duplicates)} 条重复):")
        for code, cnt in duplicates[:10]:
            print(f"   代码 {code}: 出现 {cnt} 次")
    else:
        print("\n2. 无重复数据 ✓")

    # 3. 检查缺失字段
    cur.execute("SELECT COUNT(*) FROM base_data WHERE code IS NULL OR name IS NULL OR code_converted IS NULL OR exchange IS NULL")
    missing_fields = cur.fetchone()[0]
    if missing_fields > 0:
        print(f"\n3. 发现缺失字段: {missing_fields} 条")
    else:
        print("3. 无缺失字段 ✓")

    # 4. 检查空值
    cur.execute("SELECT COUNT(*) FROM base_data WHERE code = '' OR name = '' OR code_converted = '' OR exchange = ''")
    empty_values = cur.fetchone()[0]
    if empty_values > 0:
        print(f"\n4. 发现空值: {empty_values} 条")
    else:
        print("4. 无空值 ✓")

    # 5. 检查 stock_or_fund 分布
    cur.execute("SELECT stock_or_fund, COUNT(*) FROM base_data GROUP BY stock_or_fund")
    type_dist = cur.fetchall()
    print(f"\n5. 类型分布:")
    for type_id, count in type_dist:
        type_name = "股票" if type_id == 1 else "基金"
        print(f"   {type_name} (stock_or_fund={type_id}): {count} 条")

    # 6. 检查交易所分布
    cur.execute("SELECT exchange, COUNT(*) FROM base_data GROUP BY exchange")
    exchange_dist = cur.fetchall()
    print(f"\n6. 交易所分布:")
    for exchange, count in exchange_dist:
        print(f"   {exchange}: {count} 条")

    # 7. 获取 akshare 数据进行对比
    print("\n7. 与 akshare 数据对比:")
    try:
        df = ak.stock_info_a_code_name()
        akshare_count = len(df)
        print(f"   akshare 股票数量: {akshare_count}")
        print(f"   数据库股票数量: {total_count - (type_dist[1][1] if len(type_dist) > 1 else 0)}")

        akshare_codes = set(df['code'].astype(str).tolist())
        cur.execute("SELECT code FROM base_data WHERE stock_or_fund = 1")
        db_codes = set([row[0] for row in cur.fetchall()])

        missing_in_db = akshare_codes - db_codes
        extra_in_db = db_codes - akshare_codes

        if missing_in_db:
            print(f"   数据库缺失: {len(missing_in_db)} 条")
            print(f"   缺失代码示例: {list(missing_in_db)[:5]}")
        else:
            print(f"   数据库无缺失 ✓")

        if extra_in_db:
            print(f"   数据库多余: {len(extra_in_db)} 条")
            print(f"   多余代码示例: {list(extra_in_db)[:5]}")
        else:
            print(f"   数据库无多余 ✓")

    except Exception as e:
        print(f"   对比失败: {e}")

    # 8. 示例数据
    print("\n8. 示例数据:")
    cur.execute("SELECT code, name, code_converted, exchange, stock_or_fund FROM base_data ORDER BY code LIMIT 10")
    samples = cur.fetchall()
    for row in samples:
        type_name = "股票" if row[4] == 1 else "基金"
        print(f"   {row[0]} | {row[1]} | {row[2]} | {row[3]} | {type_name}")

    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_data_quality()
