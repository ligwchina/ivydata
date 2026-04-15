import { useState, useEffect } from 'react'
import { RefreshCw, Database, LineChart, PlayCircle } from 'lucide-react'

interface StatusData {
  stockCount: number
  fundCount: number
  lastBaseDataFetch: string
  lastKlineDataFetch: string
  tasks: Task[]
}

interface Task {
  id: string
  type: string
  status: string
  startTime: string
  endTime: string
}

export default function Dashboard() {
  const [status, setStatus] = useState<StatusData>({
    stockCount: 0,
    fundCount: 0,
    lastBaseDataFetch: '从未',
    lastKlineDataFetch: '从未',
    tasks: []
  })
  const [isLoading, setIsLoading] = useState(false)

  // 从API获取状态数据
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/data/stats')
        const result = await response.json()
        if (result.success) {
          setStatus({
            stockCount: result.data.stockCount,
            fundCount: result.data.fundCount,
            lastBaseDataFetch: result.data.lastBaseDataFetch || '从未',
            lastKlineDataFetch: result.data.lastKlineDataFetch || '从未',
            tasks: []
          })
        }
      } catch (error) {
        console.error('获取状态数据失败:', error)
      }
    }

    fetchStatus()
  }, [])

  const handleFetchBaseData = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/data/base-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      const data = await response.json()
      if (data.success) {
        alert('基础数据抓取任务已开始')
      } else {
        alert('基础数据抓取任务失败: ' + data.message)
      }
    } catch (error) {
      console.error('调用API失败:', error)
      alert('调用API失败，请检查后端服务是否运行')
    } finally {
      setIsLoading(false)
    }
  }

  const handleFetchKlineData = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/data/kline-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      const data = await response.json()
      if (data.success) {
        alert('K线数据抓取任务已开始')
      } else {
        alert('K线数据抓取任务失败: ' + data.message)
      }
    } catch (error) {
      console.error('调用API失败:', error)
      alert('调用API失败，请检查后端服务是否运行')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 状态概览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">股票数量</p>
              <p className="text-2xl font-bold text-gray-800 mt-1">{status.stockCount}</p>
            </div>
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <Database className="w-5 h-5 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">基金数量</p>
              <p className="text-2xl font-bold text-gray-800 mt-1">{status.fundCount}</p>
            </div>
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <LineChart className="w-5 h-5 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">基础数据更新时间</p>
              <p className="text-sm text-gray-800 mt-1">{status.lastBaseDataFetch}</p>
            </div>
            <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
              <RefreshCw className="w-5 h-5 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">K线数据更新时间</p>
              <p className="text-sm text-gray-800 mt-1">{status.lastKlineDataFetch}</p>
            </div>
            <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
              <RefreshCw className="w-5 h-5 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* 任务管理 */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">任务管理</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={handleFetchBaseData}
            disabled={isLoading}
            className="flex items-center justify-center px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center">
                <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                执行中...
              </span>
            ) : (
              <span className="flex items-center">
                <PlayCircle className="w-5 h-5 mr-2" />
                抓取基础数据
              </span>
            )}
          </button>

          <button
            onClick={handleFetchKlineData}
            disabled={isLoading}
            className="flex items-center justify-center px-6 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center">
                <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                执行中...
              </span>
            ) : (
              <span className="flex items-center">
                <PlayCircle className="w-5 h-5 mr-2" />
                抓取K线数据
              </span>
            )}
          </button>
        </div>
      </div>

      {/* 任务历史 */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">任务历史</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">任务类型</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">开始时间</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">结束时间</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {status.tasks.map((task) => (
                <tr key={task.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${task.type === 'base-data' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                      {task.type === 'base-data' ? '基础数据' : 'K线数据'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${task.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {task.status === 'completed' ? '已完成' : '执行中'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {task.startTime}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {task.endTime}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}