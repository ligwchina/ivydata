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
        CREATE TABLE IF NOT EXISTS base_data (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            code_converted VARCHAR(20) NOT NULL,
            exchange VARCHAR(10) NOT NULL,
            stock_or_fund INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    return conn

def check_base_data():
    try:
        conn = init_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT code, name, code_converted, exchange, stock_or_fund 
            FROM base_data 
            ORDER BY stock_or_fund, code
        """)

        result = cur.fetchall()

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

        cur.close()
        conn.close()
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(check_base_data())
