import amqp, { Connection, Channel, ConsumeMessage } from 'amqplib'
import { config } from './config.js'

let connection: Connection | null = null
let channel: Channel | null = null

export async function connectRabbitMQ(): Promise<Channel> {
  if (channel) {
    return channel
  }

  try {
    connection = await amqp.connect(config.rabbitmq.url)
    channel = await connection.createChannel()
    
    await channel.assertQueue('base_data_queue', { durable: true })
    await channel.assertQueue('kline_data_queue', { durable: true })
    
    await channel.prefetch(config.rabbitmq.prefetch)
    
    console.log('Worker: RabbitMQ 连接成功')
    return channel
  } catch (error) {
    console.error('错误：RabbitMQ 消息服务器未启动！请先启动 RabbitMQ 服务。')
    console.error(`配置信息: ${config.rabbitmq.url}`)
    throw error
  }
}

export async function consumeQueue(
  queue: string,
  handler: (msg: ConsumeMessage) => Promise<void>
): Promise<void> {
  const ch = await connectRabbitMQ()
  
  await ch.consume(queue, async (msg) => {
    if (msg) {
      try {
        await handler(msg)
        ch.ack(msg)
      } catch (error) {
        console.error(`处理消息失败:`, error)
        ch.nack(msg, false, false)
      }
    }
  })
  
  console.log(`Worker: 已订阅队列 ${queue}`)
}

export async function closeRabbitMQ(): Promise<void> {
  if (channel) {
    await channel.close()
    channel = null
  }
  if (connection) {
    await connection.close()
    connection = null
  }
}
