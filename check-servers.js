import http from 'http'

// 检查服务是否可访问
function checkServer(host, port, path = '/') {
  return new Promise((resolve) => {
    const options = {
      host,
      port,
      path,
      timeout: 2000,
      method: 'GET'
    }

    const req = http.request(options, (res) => {
      resolve(res.statusCode < 500)
    })

    req.on('error', () => {
      resolve(false)
    })

    req.on('timeout', () => {
      req.destroy()
      resolve(false)
    })

    req.end()
  })
}

async function main() {
  console.log('检查服务状态...')

  // 检查 frontserver (前台服务端)
  console.log('检查前台服务端 (端口 3001)...')
  const frontserverOk = await checkServer('127.0.0.1', 3001, '/health')
  
  if (!frontserverOk) {
    console.error('❌ 错误：前台服务端未启动！')
    console.error('   请先运行: pnpm run frontserver:dev')
    process.exit(1)
  }
  console.log('✅ 前台服务端已启动')

  // 检查 backserver 不需要 HTTP 检查，因为它不监听 HTTP 端口
  // 我们只检查 RabbitMQ 是否正常工作（通过 frontserver 的健康检查）
  console.log('✅ 服务检查完成，所有必需服务都已启动')
  
  // 传递控制权给下一个命令（通过环境变量或直接退出）
  process.exit(0)
}

main()
