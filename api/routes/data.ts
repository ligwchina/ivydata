import express, { type Request, type Response, type NextFunction } from 'express'
import pool from '../db'
import { spawn } from 'child_process'

const router = express.Router()

interface BaseDataItem {
  id: number
  code: string
  name: string
  code_converted: string
  exchange: string
  stock_or_fund: number
}

interface KlineDataItem {
  id: number
  code: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}

router.get('/base-data', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { search, exchange, type, page = 1, pageSize = 20 } = req.query
    
    let query = 'SELECT * FROM base_data WHERE 1=1'
    const params: (string | number)[] = []
    let paramIndex = 1

    if (search) {
      query += ` AND (code ILIKE $${paramIndex} OR name ILIKE $${paramIndex} OR code_converted ILIKE $${paramIndex})`
      params.push(`%${search}%`)
      paramIndex++
    }

    if (exchange) {
      query += ` AND exchange = $${paramIndex}`
      params.push(exchange as string)
      paramIndex++
    }

    if (type) {
      query += ` AND stock_or_fund = $${paramIndex}`
      params.push(parseInt(type as string))
      paramIndex++
    }

    const countQuery = query.replace('SELECT *', 'SELECT COUNT(*) as total')
    const countResult = await pool.query(countQuery, params)
    const total = parseInt(countResult.rows[0]?.total || '0')

    const offset = (parseInt(page as string) - 1) * parseInt(pageSize as string)
    query += ` ORDER BY code LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`
    params.push(parseInt(pageSize as string), offset)

    const result = await pool.query<BaseDataItem>(query, params)

    res.status(200).json({
      success: true,
      data: result.rows,
      total,
      page: parseInt(page as string),
      pageSize: parseInt(pageSize as string)
    })
  } catch (error) {
    next(error)
  }
})

router.post('/base-data', (req: Request, res: Response, next: NextFunction) => {
  try {
    const pythonPath = process.cwd() + '/data/base_data.py'
    console.log('执行Python脚本:', pythonPath)
    const childProcess = spawn('python', [pythonPath], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    })

    let output = ''
    let error = ''

    childProcess.stdout.on('data', (data) => {
      const text = data.toString()
      console.log('Python stdout:', text)
      output += text
    })

    childProcess.stderr.on('data', (data) => {
      const text = data.toString()
      console.error('Python stderr:', text)
      error += text
    })

    childProcess.on('error', (err) => {
      console.error('Spawn error:', err)
    })

    childProcess.on('close', (code) => {
      console.log('Python process exited with code:', code)
      if (code === 0) {
        res.status(200).json({
          success: true,
          message: '基础数据抓取成功'
        })
      } else {
        res.status(500).json({
          success: false,
          message: '基础数据抓取失败',
          error
        })
      }
    })
  } catch (error) {
    next(error)
  }
})

router.get('/kline-data', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { code, startDate, endDate, page = 1, pageSize = 50 } = req.query
    
    if (!code) {
      const result = await pool.query(`
        SELECT DISTINCT code FROM kline_data 
        ORDER BY code 
        LIMIT 20
      `)
      return res.status(200).json({
        success: true,
        data: result.rows
      })
    }

    let query = 'SELECT * FROM kline_data WHERE code = $1'
    const params: (string | number)[] = [code as string]
    let paramIndex = 2

    if (startDate) {
      query += ` AND date >= $${paramIndex}`
      params.push(startDate as string)
      paramIndex++
    }

    if (endDate) {
      query += ` AND date <= $${paramIndex}`
      params.push(endDate as string)
      paramIndex++
    }

    const countQuery = query.replace('SELECT *', 'SELECT COUNT(*) as total')
    const countResult = await pool.query(countQuery, params)
    const total = parseInt(countResult.rows[0]?.total || '0')

    const offset = (parseInt(page as string) - 1) * parseInt(pageSize as string)
    query += ` ORDER BY date DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`
    params.push(parseInt(pageSize as string), offset)

    const result = await pool.query<KlineDataItem>(query, params)

    res.status(200).json({
      success: true,
      data: result.rows,
      total,
      page: parseInt(page as string),
      pageSize: parseInt(pageSize as string)
    })
  } catch (error) {
    next(error)
  }
})

router.post('/kline-data', (req: Request, res: Response, next: NextFunction) => {
  try {
    const pythonPath = process.cwd() + '/data/day_k_data.py'
    console.log('执行Python脚本:', pythonPath)
    const childProcess = spawn('python', [pythonPath], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    })

    let output = ''
    let error = ''

    childProcess.stdout.on('data', (data) => {
      const text = data.toString()
      console.log('Python stdout:', text)
      output += text
    })

    childProcess.stderr.on('data', (data) => {
      const text = data.toString()
      console.error('Python stderr:', text)
      error += text
    })

    childProcess.on('error', (err) => {
      console.error('Spawn error:', err)
    })

    childProcess.on('close', (code) => {
      console.log('Python process exited with code:', code)
      if (code === 0) {
        res.status(200).json({
          success: true,
          message: 'K线数据抓取成功'
        })
      } else {
        res.status(500).json({
          success: false,
          message: 'K线数据抓取失败',
          error
        })
      }
    })
  } catch (error) {
    next(error)
  }
})

router.get('/stats', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const stockResult = await pool.query(
      "SELECT COUNT(*) as count FROM base_data WHERE stock_or_fund = 1"
    )
    const fundResult = await pool.query(
      "SELECT COUNT(*) as count FROM base_data WHERE stock_or_fund = 2"
    )
    const klineResult = await pool.query(
      "SELECT COUNT(*) as count FROM kline_data"
    )
    const lastBaseResult = await pool.query(
      "SELECT MAX(updated_at) as last_update FROM base_data"
    )
    const lastKlineResult = await pool.query(
      "SELECT MAX(date) as last_date FROM kline_data"
    )

    res.status(200).json({
      success: true,
      data: {
        stockCount: parseInt(stockResult.rows[0]?.count || '0'),
        fundCount: parseInt(fundResult.rows[0]?.count || '0'),
        klineCount: parseInt(klineResult.rows[0]?.count || '0'),
        lastBaseDataFetch: lastBaseResult.rows[0]?.last_update || null,
        lastKlineDataFetch: lastKlineResult.rows[0]?.last_date || null
      }
    })
  } catch (error) {
    next(error)
  }
})

router.post('/init-db', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { initDatabase } = await import('../db.js')
    await initDatabase()
    res.status(200).json({
      success: true,
      message: '数据库初始化成功'
    })
  } catch (error) {
    next(error)
  }
})

export default router
