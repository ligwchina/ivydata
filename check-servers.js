import http from 'http'

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

  console.log('检查服务端 (端口 3001)...')
  const serverOk = await checkServer('127.0.0.1', 3001, '/health')
  
  if (!serverOk) {
    console.error('❌ 错误：服务端未启动！')
    console.error('   请先运行: pnpm run server:dev')
    process.exit(1)
  }
  console.log('✅ 服务端已启动')

  console.log('✅ 服务检查完成')
  process.exit(0)
}

main()
