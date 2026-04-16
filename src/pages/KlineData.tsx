import { useState, useEffect } from 'react'
import { Search, Download, RefreshCw, PlayCircle } from 'lucide-react'
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, Brush } from 'recharts'

interface KlineDataItem {
  code: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
}

export default function KlineData() {
  const [data, setData] = useState<KlineDataItem[]>([])
  const [filteredData, setFilteredData] = useState<KlineDataItem[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 50
  const [selectedCode, setSelectedCode] = useState('600519')
  const [chartData, setChartData] = useState<KlineDataItem[]>([])

  // 从API获取K线数据
  // 数据转换函数
  const convertData = (rawData: unknown[]): KlineItem[] => {
    return rawData.map((item: unknown) => {
      const record = item as Record<string, unknown>
      return {
        code: String(record.code || ''),
        date: String(record.date || ''),
        open: Number(record.open) || 0,
        high: Number(record.high) || 0,
        low: Number(record.low) || 0,
        close: Number(record.close) || 0,
        volume: Number(record.volume) || 0,
        amount: Number(record.amount) || 0
      }
    })
  }

  useEffect(() => {
    const fetchKlineData = async () => {
      try {
        const response = await fetch(`/api/data/kline-data?code=${selectedCode}`)
        const result = await response.json()
        if (result.success && Array.isArray(result.data)) {
          const convertedData = convertData(result.data)
          setChartData(convertedData)
          setData(convertedData)
          setFilteredData(convertedData)
        }
      } catch (error) {
        console.error('获取K线数据失败:', error)
      }
    }

    fetchKlineData()
  }, [selectedCode])

  // 搜索功能
  useEffect(() => {
    if (searchTerm) {
      const filtered = data.filter(item =>
        item.code.includes(searchTerm)
      )
      setFilteredData(filtered)
      setCurrentPage(1)
    } else {
      setFilteredData(data)
    }
  }, [searchTerm, data])

  // 分页计算
  const safeFilteredData = Array.isArray(filteredData) ? filteredData : []
  const totalPages = Math.ceil(safeFilteredData.length / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const paginatedData = safeFilteredData.slice(startIndex, startIndex + pageSize)

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

  const handleExportData = () => {
    // 这里应该实现导出功能
    alert('数据导出功能已触发')
  }

  const handleCodeChange = (code: string) => {
    setSelectedCode(code)
    // 这里应该从API获取该代码的K线数据
    const codeData = data.filter(item => item.code === code)
    setChartData(codeData)
  }

  // 安全数值格式化函数
  const formatNumber = (value: unknown, decimals = 2): string => {
    const num = Number(value)
    if (isNaN(num) || value === null || value === undefined) {
      return '-'
    }
    return num.toFixed(decimals)
  }

  const formatVolume = (value: unknown): string => {
    const num = Number(value)
    if (isNaN(num) || value === null || value === undefined) {
      return '-'
    }
    return num.toLocaleString()
  }

  return (
    <div className="space-y-6">
      {/* 操作面板 */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="搜索股票/基金代码"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleExportData}
              className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <Download className="w-4 h-4 mr-2" />
              导出数据
            </button>
            <button
              onClick={handleFetchKlineData}
              disabled={isLoading}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center">
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  执行中...
                </span>
              ) : (
                <span className="flex items-center">
                  <PlayCircle className="w-4 h-4 mr-2" />
                  抓取数据
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 数据可视化 */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-800">K线图表</h3>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">选择代码:</label>
            <select
              value={selectedCode}
              onChange={(e) => handleCodeChange(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="600519">600519 (贵州茅台)</option>
              <option value="000858">000858 (五粮液)</option>
            </select>
          </div>
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="close" stroke="#1e40af" fill="#dbeafe" />
              <Brush dataKey="date" height={30} stroke="#1e40af" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 数据列表 */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">代码</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">日期</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">开盘价</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最高价</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最低价</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">收盘价</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">成交量</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">成交额</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedData.map((item) => (
                <tr 
                  key={`${item.code}-${item.date}`}
                  onClick={() => handleCodeChange(item.code)}
                  className="cursor-pointer hover:bg-gray-50 transition-colors"
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.code}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.date}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatNumber(item.open)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatNumber(item.high)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatNumber(item.low)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatNumber(item.close)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatVolume(item.volume)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatVolume(item.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        <div className="flex items-center justify-between mt-6">
          <div className="text-sm text-gray-500">
            显示 {startIndex + 1} 到 {Math.min(startIndex + pageSize, filteredData.length)} 条，共 {filteredData.length} 条
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span className="text-sm text-gray-700">
              {currentPage} / {totalPages || 1}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages || totalPages === 0}
              className="px-3 py-1 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}