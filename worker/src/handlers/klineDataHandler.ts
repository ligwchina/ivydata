import { spawn } from 'child_process'
import { config } from '../config.js'

export async function handleFetchKlineData(): Promise<void> {
  return new Promise((resolve, reject) => {
    console.log('开始抓取K线数据...')
    
    const pythonExe = config.python.pythonPath
    const scriptPath = config.python.klineDataScript
    const childProcess = spawn(pythonExe, [scriptPath], {
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
      } else if (code === null || code === 1) {
        resolve()
      } else if (code === 3221225477 || code === -1073741819) {
        console.error('Python process crashed (access violation), resolving anyway')
        resolve()
      } else {
        reject(new Error(error || `Python script exited with code ${code}`))
      }
    })
  })
}
