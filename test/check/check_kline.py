import psycopg2
import json
import sys
import os

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'ivydata',
    'password': 'jcXz3rPjWrHY8MKF',
    'database': 'ivydata'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kline_data (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            open NUMERIC(18, 4) NOT NULL,
            high NUMERIC(18, 4) NOT NULL,
            low NUMERIC(18, 4) NOT NULL,
            close NUMERIC(18, 4) NOT NULL,
            volume BIGINT NOT NULL,
            amount NUMERIC(18, 4) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code, date)
        )
    """)
    conn.commit()
    cur.close()
    return conn

def check_kline_data(code=None):
    try:
        conn = init_db()
        cur = conn.cursor()

        if code:
            cur.execute("""
                SELECT code, date, open, high, low, close, volume, amount 
                FROM kline_data 
                WHERE code = %s
                ORDER BY date DESC
                LIMIT 50
            """, (code,))
        else:
            cur.execute("""
                SELECT code, date, open, high, low, close, volume, amount 
                FROM kline_data 
                ORDER BY code, date DESC
                LIMIT 50
            """)

        result = cur.fetchall()

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

        cur.close()
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
