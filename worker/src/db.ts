import { Pool } from 'pg'

// PostgreSQL 配置
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

console.log('PostgreSQL (读写模式) 连接池初始化成功')

// 执行查询
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

// 执行写操作（insert/update/delete）
export async function run(sql: string, params: unknown[] = []): Promise<void> {
  const client = await pool.connect()
  try {
    console.log('执行 SQL:', sql, '参数:', params)
    await client.query(sql, params)
  } finally {
    client.release()
  }
}

// 执行多条 SQL
export async function exec(sql: string): Promise<void> {
  const client = await pool.connect()
  try {
    console.log('执行 SQL:', sql)
    await client.query(sql)
  } finally {
    client.release()
  }
}

// 关闭连接池（用于程序退出时）
export async function closePool(): Promise<void> {
  await pool.end()
  console.log('PostgreSQL 连接池已关闭')
}
