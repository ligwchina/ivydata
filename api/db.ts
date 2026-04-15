import { Pool } from 'pg'
import { dbConfig } from './config/db'

const pool = new Pool({
  ...dbConfig,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})

export async function initDatabase(): Promise<void> {
  const client = await pool.connect()
  try {
    await client.query(`
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
    `)

    await client.query(`
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
    `)

    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_kline_data_code ON kline_data(code)
    `)

    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_kline_data_date ON kline_data(date)
    `)

    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_base_data_code ON base_data(code)
    `)

    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_base_data_exchange ON base_data(exchange)
    `)

    console.log('Database tables initialized successfully')
  } finally {
    client.release()
  }
}

export async function closePool(): Promise<void> {
  await pool.end()
}

export default pool
