import { existsSync } from 'fs'
import { exec as childProcessExec } from 'child_process'
import { promisify } from 'util'
import { consumeQueue } from './rabbitmq.js'
import { handleFetchBaseData } from './handlers/baseDataHandler.js'
import { handleFetchKlineData } from './handlers/klineDataHandler.js'
import { handleCheckAndFillKlineData } from './handlers/checkAndFillKlineDataHandler.js'
import { query, exec, closePool } from './db.js'
import { closeRabbitMQ } from './rabbitmq.js'
import type { ConsumeMessage } from 'amqplib'

const execAsync = promisify(childProcessExec)

// 检查通达信软件是否正在运行
async function checkTdxRunning(): Promise<boolean> {
  const tdxPath = 'D:\\new_tdx64\\tdxw.exe'
  
  // 检查文件是否存在
  if (!existsSync(tdxPath)) {
    console.error(`通达信软件不存在: ${tdxPath}`)
    return false
  }
  
  try {
    // 使用 wmic 检查进程是否正在运行
    const { stdout } = await execAsync('wmic process where "name=\'tdxw.exe\'" get name')
    return stdout.includes('tdxw.exe')
  } catch (error) {
    console.error('检查通达信进程失败:', error)
    return false
  }
}

async function handleMessage(msg: ConsumeMessage): Promise<void> {
  const content = JSON.parse(msg.content.toString())
  console.log('收到消息:', content)

  switch (content.action) {
    case 'fetch_base_data':
      await handleFetchBaseData()
      break
    case 'fetch_kline_data':
      await handleFetchKlineData()
      break
    case 'check_and_fill_kline_data':
      await handleCheckAndFillKlineData(content.code)
      break
    default:
      console.warn('未知消息类型:', content.action)
  }
}

async function start() {
  console.log('后台服务启动中...')

  // 检查通达信软件是否正在运行
  const tdxRunning = await checkTdxRunning()
  if (!tdxRunning) {
    console.error('错误：通达信软件未启动！请先启动通达信软件 D:\\new_tdx64\\tdxw.exe')
    console.error('后台服务启动失败。')
    process.exit(1)
  }
  console.log('通达信软件检查通过，正在运行中...')

  // 检查并创建数据库表
  console.log('检查并初始化数据库表结构...')
  
  // 检查 base_data 表是否存在
  const checkTableResult = await query(`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_name = 'base_data'
    )
  `)
  const tableExists = (checkTableResult[0] as Record<string, unknown>).exists
  
  if (!tableExists) {
    console.log('创建 base_data 表...')
    await exec(`
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
  
  // 检查 kline_data 表是否存在
  const checkKlineTableResult = await query(`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_name = 'kline_data'
    )
  `)
  const klineTableExists = (checkKlineTableResult[0] as Record<string, unknown>).exists
  
  if (!klineTableExists) {
    console.log('创建 kline_data 表...')
    await exec(`
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
  
  console.log('数据库表结构初始化完成')

  await consumeQueue('base_data_queue', handleMessage)
  await consumeQueue('kline_data_queue', handleMessage)

  console.log('后台服务已启动，等待消息...')
}

async function shutdown() {
  console.log('正在关闭后台服务...')
  await closeRabbitMQ()
  await closePool()
  process.exit(0)
}

process.on('SIGINT', shutdown)
process.on('SIGTERM', shutdown)

start().catch(console.error)
