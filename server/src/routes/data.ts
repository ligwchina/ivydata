import { Router, Request, Response } from 'express'
import { query } from '../db'

const router = Router()

router.get('/stats', async (req: Request, res: Response) => {
  try {
    const stockResult = await query(
      'SELECT COUNT(*) as count FROM base_data WHERE stock_or_fund = 1'
    )
    const stockRow = stockResult[0] as Record<string, unknown>
    const stockCount = Number(stockRow.count) || 0
    
    const fundResult = await query(
      'SELECT COUNT(*) as count FROM base_data WHERE stock_or_fund = 2'
    )
    const fundRow = fundResult[0] as Record<string, unknown>
    const fundCount = Number(fundRow.count) || 0
    
    const sysOptionsResult = await query(
      "SELECT option_key, option_value FROM sys_options WHERE option_key IN ('last_base_data_fetch', 'last_kline_data_fetch')"
    )
    
    let lastBaseDataFetch = '从未'
    let lastKlineDataFetch = '从未'
    
    for (const row of sysOptionsResult as Array<Record<string, unknown>>) {
      if (row.option_key === 'last_base_data_fetch' && row.option_value) {
        lastBaseDataFetch = String(row.option_value)
      }
      if (row.option_key === 'last_kline_data_fetch' && row.option_value) {
        lastKlineDataFetch = String(row.option_value)
      }
    }
    
    res.json({
      success: true,
      data: {
        stockCount: stockCount,
        fundCount: fundCount,
        lastBaseDataFetch: lastBaseDataFetch,
        lastKlineDataFetch: lastKlineDataFetch
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
    
    const countResult = await query(
      'SELECT COUNT(*) as total FROM base_data' + whereClause,
      params
    )
    const countRow = countResult[0] as Record<string, unknown>
    const total = Number(countRow.total) || 0
    
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

router.get('/kline-data/check', async (req: Request, res: Response) => {
  try {
    const code = (req.query.code as string) || ''
    
    console.log('检查K线数据完整性:', { code })
    
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
      const dateRangeResult = await query(
        'SELECT MIN(date) as min_date, MAX(date) as max_date FROM kline_data WHERE code = $1',
        [c]
      )
      const dateRow = dateRangeResult[0] as Record<string, string>
      
      if (!dateRow.min_date || !dateRow.max_date) {
        continue
      }
      
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

export default router
