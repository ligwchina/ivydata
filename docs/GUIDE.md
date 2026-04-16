# IvyData - 股票数据分析系统

一个基于 React + TypeScript + PostgreSQL 的股票数据分析系统。

## 系统架构

本系统采用两部分架构，使用 PostgreSQL 作为主数据库：

```
┌─────────────┐
│   前端      │ (React + TypeScript + TailwindCSS)
│             │ http://localhost:5173
└──────┬──────┘
       │ HTTP
       ▼
┌────────────────────┐
│  服务端            │ (Node.js + Express + TypeScript)
│                    │ http://localhost:3001
│  * PostgreSQL     │
│  * 调用Python脚本  │
└──────┬─────────────┘
       │
       ▼
┌────────────────────┐
│  PostgreSQL 数据库 │ 127.0.0.1:5432
│                    │
│  数据库: ivydata   │
│  用户: ivydata     │
└────────────────────┘
       │
       ▼
┌────────────────────┐
│  通达信软件        │ D:\new_tdx64\tdxw.exe
└────────────────────┘
```

## 技术栈

### 前端
- React 18
- TypeScript
- Vite
- TailwindCSS
- Recharts (图表)
- React Router (路由)

### 服务端
- Node.js
- Express.js
- TypeScript
- pg (PostgreSQL 客户端)
- Python 脚本 (数据抓取)

### 数据抓取
- 直接写入 PostgreSQL（使用批量插入优化）

### 基础设施
- PostgreSQL (关系型数据库)

## 安装和配置

### 前置要求

1. **Node.js 18+** 和 **pnpm**
2. **PostgreSQL** (默认配置: 127.0.0.1:5432, 数据库: ivydata, 用户: ivydata)
3. **通达信软件** (路径: D:\new_tdx64\tdxw.exe) - 数据抓取需要
4. **Python 3+** (数据抓取脚本需要)

### Python 依赖

```bash
pip install psycopg2-binary akshare pandas
```

### 安装依赖

```bash
pnpm install
```

## 启动服务

### 完整启动流程（推荐）

1. **确保 PostgreSQL 服务已启动**
2. **确保通达信软件已启动**（数据抓取需要）
3. **启动服务端**：
   ```bash
   pnpm run server:dev
   ```
4. **启动前端开发服务器**：
   ```bash
   pnpm run client:dev
   ```

### 快速启动

同时启动前端和服务端：
```bash
pnpm run dev
```

### 单独启动各服务

| 服务 | 命令 | 说明 |
|------|------|------|
| 前端 | `pnpm run client:dev` | http://localhost:5173 |
| 服务端 | `pnpm run server:dev` | http://localhost:3001 |

## 目录结构

```
ivydata/
├── src/                  # 前端源代码
│   ├── components/       # 组件
│   ├── pages/            # 页面
│   ├── App.tsx
│   └── main.tsx
├── server/              # 服务端
│   ├── src/
│   │   ├── routes/      # API 路由
│   │   ├── db.ts        # 数据库连接
│   │   └── index.ts     # 入口
│   └── package.json
├── data/                # Python 数据抓取脚本
│   ├── base_data_with_duckdb.py    # 基础数据抓取
│   ├── day_k_data_with_duckdb.py   # K线数据抓取
│   ├── check_and_fill_kline_data.py # K线数据检查和补充
│   └── ...
├── test/                # 测试文件
│   ├── check/           # 检查脚本
│   ├── base/            # 基础测试
│   └── tdx/             # 通达信测试
├── package.json
└── README.md
```

## 数据抓取

数据抓取需要手动运行 Python 脚本：

```bash
# 激活 Python 环境
conda activate myenv311

# 抓取基础数据（股票+基金）
python data/base_data_with_duckdb.py

# 抓取K线数据
python data/day_k_data_with_duckdb.py

# 检查并补充K线数据
python data/check_and_fill_kline_data.py
```

## API 接口

### 服务端 (http://localhost:3001)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/data/stats` | 获取统计数据 |
| GET | `/api/data/base-data` | 获取基础数据 |
| GET | `/api/data/kline-data` | 获取 K 线数据 |
| GET | `/api/data/kline-data/check` | 检查 K 线数据完整性 |

## 配置说明

### PostgreSQL 配置

**数据库信息**：
- 主机: `127.0.0.1`
- 端口: `5432`
- 数据库: `ivydata`
- 用户: `ivydata`
- 密码: `jcXz3rPjWrHY8MKF`

### Python 配置

数据抓取脚本使用 `myenv311` conda 环境，需要确保以下依赖已安装：
- psycopg2-binary
- akshare
- pandas

### 通达信软件路径

- 路径: `D:\new_tdx64\tdxw.exe`

## 服务端启动检查

服务启动时会自动进行以下检查：

1. ✅ PostgreSQL 连接
2. ✅ 数据库表初始化

## 数据库表结构

服务端首次启动时会自动创建以下表：

1. **base_data** - 基础数据（股票/基金列表）
2. **kline_data** - K 线数据
3. **grab_record** - 抓取记录

## 测试和检查

### 运行检查脚本

```bash
cd test/check

# 检查 PostgreSQL 连接
python check_postgres_connection.py

# 完整项目检查
python check_all.py

# 清空数据库表
python clear_postgres_tables.py
```

## 故障排除

如果遇到问题，请检查：

1. PostgreSQL 服务是否正常运行
2. 通达信软件是否已启动
3. Python 环境是否正确激活
4. 依赖包是否已安装
