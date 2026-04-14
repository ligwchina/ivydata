import { useState, useEffect } from 'react'
import { Search, Download, RefreshCw, PlayCircle } from 'lucide-react'

interface BaseDataItem {
  code: string
  name: string
  code_converted: string
  exchange: string
  stock_or_fund: number
}

export default function BaseData() {
  const [data, setData] = useState<BaseDataItem[]>([])
  const [filteredData, setFilteredData] = useState<BaseDataItem[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // 从API获取基础数据
  useEffect(() => {
    const fetchBaseData = async () => {
      try {
        const response = await fetch('/api/data/base-data')
        const data = await response.json()
        if (data.success) {
          setData(data.data)
          setFilteredData(data.data)
        } else {
          console.error('获取基础数据失败:', data.message)
          // 使用模拟数据作为 fallback
          const mockData: BaseDataItem[] = [
            { code: '600519', name: '贵州茅台', code_converted: '600519.SH', exchange: 'SH', stock_or_fund: 1 },
            { code: '000858', name: '五粮液', code_converted: '000858.SZ', exchange: 'SZ', stock_or_fund: 1 },
            { code: '000001', name: '平安银行', code_converted: '000001.SZ', exchange: 'SZ', stock_or_fund: 1 },
            { code: '510050', name: '50ETF', code_converted: '510050.SH', exchange: 'SH', stock_or_fund: 2 },
            { code: '513050', name: '中概互联', code_converted: '513050.SH', exchange: 'SH', stock_or_fund: 2 }
          ]
          setData(mockData)
          setFilteredData(mockData)
        }
      } catch (error) {
        console.error('调用API失败:', error)
        // 使用模拟数据作为 fallback
        const mockData: BaseDataItem[] = [
          { code: '600519', name: '贵州茅台', code_converted: '600519.SH', exchange: 'SH', stock_or_fund: 1 },
          { code: '000858', name: '五粮液', code_converted: '000858.SZ', exchange: 'SZ', stock_or_fund: 1 },
          { code: '000001', name: '平安银行', code_converted: '000001.SZ', exchange: 'SZ', stock_or_fund: 1 },
          { code: '510050', name: '50ETF', code_converted: '510050.SH', exchange: 'SH', stock_or_fund: 2 },
          { code: '513050', name: '中概互联', code_converted: '513050.SH', exchange: 'SH', stock_or_fund: 2 }
        ]
        setData(mockData)
        setFilteredData(mockData)
      }
    }

    fetchBaseData()
  }, [])

  // 搜索功能
  useEffect(() => {
    if (searchTerm) {
      const filtered = data.filter(item =>
        item.code.includes(searchTerm) ||
        item.name.includes(searchTerm) ||
        item.code_converted.includes(searchTerm)
      )
      setFilteredData(filtered)
      setCurrentPage(1)
    } else {
      setFilteredData(data)
    }
  }, [searchTerm, data])

  // 分页计算
  const totalPages = Math.ceil(filteredData.length / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const paginatedData = filteredData.slice(startIndex, startIndex + pageSize)

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

  const handleExportData = () => {
    // 这里应该实现导出功能
    alert('数据导出功能已触发')
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
                placeholder="搜索代码、名称"
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
              onClick={handleFetchBaseData}
              disabled={isLoading}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
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

      {/* 数据列表 */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">代码</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">名称</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">带后缀代码</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">交易所</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedData.map((item) => (
                <tr key={item.code}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.code}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.code_converted}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.exchange}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${item.stock_or_fund === 1 ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                      {item.stock_or_fund === 1 ? '股票' : '基金'}
                    </span>
                  </td>
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