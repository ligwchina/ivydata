import express from 'express'
import cors from 'cors'
import dataRouter from './routes/data'
import { initRabbitMQ } from './services/rabbitmq'

const app = express()
const PORT = 3001

// 中间件
app.use(cors())
app.use(express.json())

// 路由
app.use('/api/data', dataRouter)

// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'ok' })
})

async function start() {
  try {
    // 初始化 RabbitMQ
    await initRabbitMQ()
    
    // 启动服务器
    app.listen(PORT, () => {
      console.log(`前台服务端已启动: http://localhost:${PORT}`)
    })
  } catch (error) {
    console.error('启动失败:', error)
    process.exit(1)
  }
}

start()
