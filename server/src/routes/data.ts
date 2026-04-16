import { Router, Request, Response } from 'express'
import { query } from '../db'
import { sendToQueue, QUEUE_NAMES } from '../services/rabbitmq'

const router = Router()

// 获取统计数据
router.get('/stats', async (req: Request, res: Response) => {
  try {
    // 获取股票数量
    const stockResult = await query(
      'SELECT COUNT(*) as count FROM base_data WHERE stock_or_fund = 1'
    )
    const stockRow = stockResult[0] as Record<string, unknown>
    const stockCount = Number(stockRow.count) || 0
    
    // 获取基金数量
    const fundResult = await query(
      'SELECT COUNT(*) as count FROM base_data WHERE stock_or_fund = 2'
    )
    const fundRow = fundResult[0] as Record<string, unknown>
    const fundCount = Number(fundRow.count) || 0
    
    // 获取最后更新时间
    const lastUpdateResult = await query(
      'SELECT MAX(updated_at) as "lastUpdate" FROM base_data'
    )
    const lastUpdateRow = lastUpdateResult[0] as Record<string, unknown>
    const lastUpdate = lastUpdateRow.lastUpdate ? String(lastUpdateRow.lastUpdate) : '从未'
    
    res.json({
      success: true,
      data: {
        stockCount: stockCount,
        fundCount: fundCount,
        lastBaseDataFetch: lastUpdate,
        lastKlineDataFetch: '从未'
      }
    })
  } catch (error) {
    console.error('查询统计数据失败:', error)
    res.status(500).json({
      success: false,
      message: '查询失败',
      error: (error as Error).message
    })
  }
})

// 获取基础数据
router.get('/base-data', async (req: Request, res: Response) => {
  try {
    const page = parseInt(req.query.page as string) || 1
    const pageSize = parseInt(req.query.pageSize as string) || 20
    const search = (req.query.search as string) || ''
    const type = (req.query.type as string) || ''
    
    console.log('查询基础数据:', { page, pageSize, search, type })
    
    let whereClause = ''
    const params: unknown[] = []
    
    if (search) {
      whereClause += ' WHERE (name LIKE $1 OR code LIKE $2)'
      params.push('%' + search + '%', '%' + search + '%')
    }
    
    if (type) {
      const typeParamIndex = params.length + 1
      if (whereClause) {
        whereClause += ' AND stock_or_fund = $' + typeParamIndex
      } else {
        whereClause += ' WHERE stock_or_fund = $' + typeParamIndex
      }
      params.push(type)
    }
    
    // 获取总数
    const countResult = await query(
      'SELECT COUNT(*) as total FROM base_data' + whereClause,
      params
    )
    const countRow = countResult[0] as Record<string, unknown>
    const total = Number(countRow.total) || 0
    
    // 获取数据
    const offset = (page - 1) * pageSize
    const limitParamIndex = params.length + 1
    const offsetParamIndex = params.length + 2
    const dataParams = [...params, pageSize, offset]
    const data = await query(
      'SELECT * FROM base_data' + whereClause + ' ORDER BY id LIMIT $' + limitParamIndex + ' OFFSET $' + offsetParamIndex,
      dataParams
    )
    
    res.json({
      success: true,
      data,
      total,
      page,
      pageSize
    })
  } catch (error) {
    console.error('查询基础数据失败:', error)
    res.status(500).json({
      success: false,
      message: '查询失败',
      error: (error as Error).message
    })
  }
})

// 抓取基础数据（发送消息到队列）
router.post('/base-data', (req: Request, res: Response) => {
  try {
    console.log('收到抓取基础数据请求')
    sendToQueue(QUEUE_NAMES.BASE_DATA, { action: 'fetch_base_data' })
    res.json({
      success: true,
      message: '抓取任务已提交'
    })
  } catch (error) {
    console.error('提交抓取任务失败:', error)
    res.status(500).json({
      success: false,
      message: '提交失败',
      error: (error as Error).message
    })
  }
})

// 获取K线数据
router.get('/kline-data', async (req: Request, res: Response) => {
  try {
    const code = (req.query.code as string) || ''
    
    console.log('查询K线数据:', { code })
    
    let whereClause = ''
    const params: unknown[] = []
    
    if (code) {
      whereClause = ' WHERE code = $1'
      params.push(code)
    }
    
    // 获取数据
    const data = await query(
      'SELECT code, date, open, high, low, close, volume, amount FROM kline_data' + whereClause + ' ORDER BY date DESC LIMIT 1000',
      params
    )
    
    res.json({
      success: true,
      data
    })
  } catch (error) {
    console.error('查询K线数据失败:', error)
    res.status(500).json({
      success: false,
      message: '查询失败',
      error: (error as Error).message
    })
  }
})

// 抓取K线数据（发送消息到队列）
router.post('/kline-data', (req: Request, res: Response) => {
  try {
    console.log('收到抓取K线数据请求')
    sendToQueue(QUEUE_NAMES.KLINE_DATA, { action: 'fetch_kline_data' })
    res.json({
      success: true,
      message: '抓取任务已提交'
    })
  } catch (error) {
    console.error('提交抓取任务失败:', error)
    res.status(500).json({
      success: false,
      message: '提交失败',
      error: (error as Error).message
    })
  }
})

// 检查K线数据完整性
router.get('/kline-data/check', async (req: Request, res: Response) => {
  try {
    const code = (req.query.code as string) || ''
    
    console.log('检查K线数据完整性:', { code })
    
    // 获取所有有K线数据的代码
    let codesResult: unknown[] = []
    if (code) {
      codesResult = await query(
        'SELECT DISTINCT code FROM kline_data WHERE code = $1 ORDER BY code',
        [code]
      )
    } else {
      codesResult = await query(
        'SELECT DISTINCT code FROM kline_data ORDER BY code'
      )
    }
    
    const codes = codesResult.map((row: unknown) => (row as Record<string, string>).code)
    
    const results = []
    
    for (const c of codes) {
      // 获取该代码的K线日期范围
      const dateRangeResult = await query(
        'SELECT MIN(date) as min_date, MAX(date) as max_date FROM kline_data WHERE code = $1',
        [c]
      )
      const dateRow = dateRangeResult[0] as Record<string, string>
      
      if (!dateRow.min_date || !dateRow.max_date) {
        continue
      }
      
      // 获取该代码的所有K线日期
      const existingDatesResult = await query(
        'SELECT date FROM kline_data WHERE code = $1 ORDER BY date',
        [c]
      )
      const existingDates = existingDatesResult.map((row: unknown) => (row as Record<string, string>).date)
      
      results.push({
        code: c,
        minDate: dateRow.min_date,
        maxDate: dateRow.max_date,
        totalRecords: existingDates.length,
        existingDates: existingDates
      })
    }
    
    res.json({
      success: true,
      data: results
    })
  } catch (error) {
    console.error('检查K线数据完整性失败:', error)
    res.status(500).json({
      success: false,
      message: '检查失败',
      error: (error as Error).message
    })
  }
})

// 检查并补充K线数据（发送消息到队列）
router.post('/kline-data/check', (req: Request, res: Response) => {
  try {
    const { code } = req.body as { code?: string }
    console.log('收到检查并补充K线数据请求:', { code })
    sendToQueue(QUEUE_NAMES.KLINE_DATA, { 
      action: 'check_and_fill_kline_data',
      code: code || null
    })
    res.json({
      success: true,
      message: '检查并补充任务已提交'
    })
  } catch (error) {
    console.error('提交检查并补充任务失败:', error)
    res.status(500).json({
      success: false,
      message: '提交失败',
      error: (error as Error).message
    })
  }
})

export default router
