import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Home, Database, LineChart } from 'lucide-react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const navItems = [
    { path: '/', label: '仪表盘', icon: Home },
    { path: '/base-data', label: '基础数据', icon: Database },
    { path: '/kline-data', label: 'K线数据', icon: LineChart }
  ]

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* 侧边导航栏 */}
      <div className="w-64 bg-white shadow-md">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-blue-800">股票数据管理</h1>
        </div>
        <nav className="mt-6">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center px-6 py-3 text-gray-600 hover:bg-blue-50 hover:text-blue-800 transition-colors ${isActive ? 'bg-blue-100 text-blue-800 font-medium' : ''}`}
              >
                <Icon className="w-5 h-5 mr-3" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </div>

      {/* 主内容区域 */}
      <div className="flex-1 flex flex-col">
        {/* 顶部导航栏 */}
        <header className="bg-white shadow-sm px-6 py-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-800">
              {navItems.find(item => location.pathname === item.path)?.label || '仪表盘'}
            </h2>
            <div className="flex items-center space-x-4">
              <button className="text-gray-600 hover:text-blue-800 transition-colors">
                帮助
              </button>
            </div>
          </div>
        </header>

        {/* 内容区域 */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}