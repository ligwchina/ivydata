import express, { type Request, type Response, type NextFunction } from 'express'
import { spawn } from 'child_process'
import path from 'path'

const router = express.Router()

// 抓取基础数据
router.post('/base-data', (req: Request, res: Response, next: NextFunction) => {
  try {
    const pythonPath = path.join(process.cwd(), 'data', 'base_data.py')
    const childProcess = spawn('python3', [pythonPath])

    let output = ''
    let error = ''

    childProcess.stdout.on('data', (data) => {
      output += data.toString()
    })

    childProcess.stderr.on('data', (data) => {
      error += data.toString()
    })

    childProcess.on('close', (code) => {
      if (code === 0) {
        res.status(200).json({
          success: true,
          message: '基础数据抓取成功',
          output
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

// 抓取K线数据
router.post('/kline-data', (req: Request, res: Response, next: NextFunction) => {
  try {
    const pythonPath = path.join(process.cwd(), 'data', 'day_k_data.py')
    const childProcess = spawn('python3', [pythonPath])

    let output = ''
    let error = ''

    childProcess.stdout.on('data', (data) => {
      output += data.toString()
    })

    childProcess.stderr.on('data', (data) => {
      error += data.toString()
    })

    childProcess.on('close', (code) => {
      if (code === 0) {
        res.status(200).json({
          success: true,
          message: 'K线数据抓取成功',
          output
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

// 获取基础数据列表
router.get('/base-data', (req: Request, res: Response, next: NextFunction) => {
  try {
    const pythonPath = path.join(process.cwd(), 'data', 'check_base.py')
    const childProcess = spawn('python3', [pythonPath])

    let output = ''
    let error = ''

    childProcess.stdout.on('data', (data) => {
      output += data.toString()
    })

    childProcess.stderr.on('data', (data) => {
      error += data.toString()
    })

    childProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const data = JSON.parse(output)
          res.status(200).json({
            success: true,
            data
          })
        } catch (parseError) {
          res.status(500).json({
            success: false,
            message: '数据解析失败',
            error: parseError.message
          })
        }
      } else {
        res.status(500).json({
          success: false,
          message: '获取基础数据失败',
          error
        })
      }
    })
  } catch (error) {
    next(error)
  }
})

// 获取K线数据
router.get('/kline-data', (req: Request, res: Response, next: NextFunction) => {
  try {
    const { code } = req.query
    const pythonPath = path.join(process.cwd(), 'data', 'check_kline.py')
    const childProcess = spawn('python3', [pythonPath, code as string])

    let output = ''
    let error = ''

    childProcess.stdout.on('data', (data) => {
      output += data.toString()
    })

    childProcess.stderr.on('data', (data) => {
      error += data.toString()
    })

    childProcess.on('close', (code) => {
      if (code === 0) {
        try {
          const data = JSON.parse(output)
          res.status(200).json({
            success: true,
            data
          })
        } catch (parseError) {
          res.status(500).json({
            success: false,
            message: '数据解析失败',
            error: parseError.message
          })
        }
      } else {
        res.status(500).json({
          success: false,
          message: '获取K线数据失败',
          error
        })
      }
    })
  } catch (error) {
    next(error)
  }
})

export default router
