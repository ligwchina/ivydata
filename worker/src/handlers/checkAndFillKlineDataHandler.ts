import { spawn } from 'child_process'
import { config } from '../config.js'

export async function handleCheckAndFillKlineData(code?: string): Promise<void> {
  return new Promise((resolve, reject) => {
    console.log('开始检查并补充K线数据...')
    if (code) {
      console.log('指定代码:', code)
    }
    
    const pythonPath = config.python.checkAndFillKlineDataScript
    const args = [pythonPath]
    if (code) {
      args.push('--code', code)
    }
    
    const childProcess = spawn('python', args, {
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
      reject(err)
    })

    childProcess.on('close', (code) => {
      console.log('Python process exited with code:', code)
      if (code === 0) {
        resolve()
      } else {
        reject(new Error(error || `Python script exited with code ${code}`))
      }
    })
  })
}
