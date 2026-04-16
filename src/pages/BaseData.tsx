import { useState, useEffect } from 'react'
import { Search, Download } from 'lucide-react'

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
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 20

  useEffect(() => {
    const fetchBaseData = async () => {
      try {
        const response = await fetch('/api/data/base-data')
        const result = await response.json()
        if (result.success && Array.isArray(result.data)) {
          setData(result.data)
          setFilteredData(result.data)
        }
      } catch (error) {
        console.error('获取基础数据失败:', error)
      }
    }

    fetchBaseData()
  }, [])

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

  const safeFilteredData = Array.isArray(filteredData) ? filteredData : []
  const totalPages = Math.ceil(safeFilteredData.length / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const paginatedData = safeFilteredData.slice(startIndex, startIndex + pageSize)

  const handleExportData = () => {
    alert('数据导出功能已触发')
  }

  return (
    <div className="space-y-6">
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
          </div>
        </div>
      </div>

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
