import express from 'express'
import cors from 'cors'
import dataRouter from './routes/data'
import { query, runExec } from './db'

const app = express()
const PORT = 3001

app.use(cors())
app.use(express.json())

app.use('/api/data', dataRouter)

app.get('/health', (req, res) => {
  res.json({ status: 'ok' })
})

async function initDatabase() {
  console.log('检查并初始化数据库表结构...')

  const checkTableResult = await query(`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_name = 'base_data'
    )
  `)
  const tableExists = (checkTableResult[0] as Record<string, unknown>).exists
  
  if (!tableExists) {
    console.log('创建 base_data 表...')
    await runExec(`
      CREATE TABLE base_data (
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
    console.log('base_data 表创建成功')
  }
  
  const checkKlineTableResult = await query(`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_name = 'kline_data'
    )
  `)
  const klineTableExists = (checkKlineTableResult[0] as Record<string, unknown>).exists
  
  if (!klineTableExists) {
    console.log('创建 kline_data 表...')
    await runExec(`
      CREATE TABLE kline_data (
        id SERIAL PRIMARY KEY,
        code VARCHAR(20) NOT NULL,
        date DATE NOT NULL,
        open NUMERIC(10, 2),
        high NUMERIC(10, 2),
        low NUMERIC(10, 2),
        close NUMERIC(10, 2),
        volume BIGINT,
        amount NUMERIC(20, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(code, date)
      )
    `)
    console.log('kline_data 表创建成功')
  }
  
  const checkGrabRecordTableResult = await query(`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_name = 'grab_record'
    )
  `)
  const grabRecordTableExists = (checkGrabRecordTableResult[0] as Record<string, unknown>).exists
  
  if (!grabRecordTableExists) {
    console.log('创建 grab_record 表...')
    await runExec(`
      CREATE TABLE grab_record (
        id SERIAL PRIMARY KEY,
        type VARCHAR(50) NOT NULL,
        status VARCHAR(20) NOT NULL,
        message TEXT,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `)
    console.log('grab_record 表创建成功')
  }
  
  const checkSysOptionsTableResult = await query(`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_name = 'sys_options'
    )
  `)
  const sysOptionsTableExists = (checkSysOptionsTableResult[0] as Record<string, unknown>).exists
  
  if (!sysOptionsTableExists) {
    console.log('创建 sys_options 表...')
    await runExec(`
      CREATE TABLE sys_options (
        id SERIAL PRIMARY KEY,
        option_key VARCHAR(100) NOT NULL UNIQUE,
        option_value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `)
    
    await runExec(`
      INSERT INTO sys_options (option_key, option_value)
      VALUES 
        ('last_base_data_fetch', NULL),
        ('last_kline_data_fetch', NULL)
    `)
    console.log('sys_options 表创建成功')
  }
  
  console.log('数据库表结构初始化完成')
}

async function start() {
  try {
    await initDatabase()
    
    app.listen(PORT, () => {
      console.log(`Server 服务已启动: http://localhost:${PORT}`)
    })
  } catch (error) {
    console.error('启动失败:', error)
    process.exit(1)
  }
}

start()
