import { useState, useEffect } from 'react'
import { Database, LineChart } from 'lucide-react'

interface StatusData {
  stockCount: number
  fundCount: number
  lastBaseDataFetch: string
  lastKlineDataFetch: string
}

export default function Dashboard() {
  const [status, setStatus] = useState<StatusData>({
    stockCount: 0,
    fundCount: 0,
    lastBaseDataFetch: '从未',
    lastKlineDataFetch: '从未'
  })

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
            lastKlineDataFetch: result.data.lastKlineDataFetch || '从未'
          })
        }
      } catch (error) {
        console.error('获取状态数据失败:', error)
      }
    }

    fetchStatus()
  }, [])

  return (
    <div className="space-y-6">
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
              <Database className="w-5 h-5 text-purple-600" />
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
              <LineChart className="w-5 h-5 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">数据说明</h3>
        <p className="text-gray-600">
          本页面展示数据库中的基础统计数据。数据抓取需要手动运行 Python 脚本。
        </p>
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-800 mb-2">数据抓取命令：</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• 抓取基础数据：<code className="bg-gray-200 px-2 py-1 rounded">python data/base_data_with_duckdb.py</code></li>
            <li>• 抓取K线数据：<code className="bg-gray-200 px-2 py-1 rounded">python data/day_k_data_with_duckdb.py</code></li>
          </ul>
        </div>
      </div>
    </div>
  )
}
