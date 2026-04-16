import amqp from 'amqplib'
import { RABBITMQ_CONFIG, QUEUE_NAMES } from '../config'

let channel: amqp.Channel | null = null

export async function initRabbitMQ(): Promise<void> {
  try {
    const connection = await amqp.connect({
      hostname: RABBITMQ_CONFIG.host,
      port: RABBITMQ_CONFIG.port,
      username: RABBITMQ_CONFIG.username,
      password: RABBITMQ_CONFIG.password
    })
    channel = await connection.createChannel()
    
    // 声明队列
    await channel.assertQueue(QUEUE_NAMES.BASE_DATA, { durable: true })
    await channel.assertQueue(QUEUE_NAMES.KLINE_DATA, { durable: true })
    
    console.log('Server: RabbitMQ 连接成功')
  } catch (error) {
    console.error('错误：RabbitMQ 消息服务器未启动！请先启动 RabbitMQ 服务。')
    console.error(`配置信息: ${RABBITMQ_CONFIG.host}:${RABBITMQ_CONFIG.port}`)
    throw error
  }
}

export function sendToQueue(queueName: string, message: object): void {
  if (!channel) {
    throw new Error('RabbitMQ channel not initialized')
  }
  
  channel.sendToQueue(queueName, Buffer.from(JSON.stringify(message)), {
    persistent: true
  })
  console.log(`Server: 已发送消息到队列 ${queueName}:`, message)
}

export { QUEUE_NAMES }
