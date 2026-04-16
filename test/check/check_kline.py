import duckdb
import json
import sys
import os

DB_PATH = 'D:\\dev\\ai\\ivydata\\db\\ivy.duckdb'

def get_db_connection():
    return duckdb.connect(DB_PATH)

def check_kline_data(code=None):
    try:
        conn = get_db_connection()

        if code:
            result = conn.execute("""
                SELECT code, date, open, high, low, close, volume, amount 
                FROM kline_data 
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 50
            """, (code,)).fetchall()
        else:
            result = conn.execute("""
                SELECT code, date, open, high, low, close, volume, amount 
                FROM kline_data 
                ORDER BY code, date DESC
                LIMIT 50
            """).fetchall()

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

        sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(kline_data, ensure_ascii=False))

        conn.close()
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return 1

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(check_kline_data(code))
