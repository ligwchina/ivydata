import { Pool } from 'pg'

const pool = new Pool({
  host: '127.0.0.1',
  port: 5432,
  database: 'ivydata',
  user: 'ivydata',
  password: 'jcXz3rPjWrHY8MKF',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})

console.log('PostgreSQL 连接池初始化成功')

export async function query(sql: string, params: unknown[] = []): Promise<unknown[]> {
  const client = await pool.connect()
  try {
    console.log('执行 SQL:', sql, '参数:', params)
    const result = await client.query(sql, params)
    return result.rows
  } finally {
    client.release()
  }
}

export async function runExec(sql: string, params: unknown[] = []): Promise<void> {
  const client = await pool.connect()
  try {
    console.log('执行 SQL:', sql, '参数:', params)
    await client.query(sql, params)
  } finally {
    client.release()
  }
}

export async function closePool(): Promise<void> {
  await pool.end()
  console.log('PostgreSQL 连接池已关闭')
}
