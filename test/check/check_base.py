import duckdb
import json
import sys
import os

DB_PATH = 'D:\\dev\\ai\\ivydata\\db\\ivy.duckdb'

def get_db_connection():
    return duckdb.connect(DB_PATH)

def check_base_data():
    try:
        conn = get_db_connection()

        result = conn.execute("""
            SELECT code, name, code_converted, exchange, stock_or_fund 
            FROM base_data 
            ORDER BY stock_or_fund, code
        """).fetchall()

        base_data = []
        for row in result:
            base_data.append({
                'code': row[0],
                'name': row[1],
                'code_converted': row[2],
                'exchange': row[3],
                'stock_or_fund': row[4]
            })

        sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(base_data, ensure_ascii=False))

        conn.close()
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(check_base_data())
