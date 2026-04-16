# IvyData - 股票数据分析系统

一个基于 React + TypeScript + PostgreSQL + RabbitMQ 的股票数据分析系统。

## 系统架构

本系统采用三部分架构，使用 PostgreSQL 作为主数据库：

```
┌─────────────┐
│   前端      │ (React + TypeScript + TailwindCSS)
│             │ http://localhost:5173
└──────┬──────┘
       │ HTTP
       ▼
┌────────────────────┐
│  前台服务端        │ (Node.js + Express + TypeScript)
│                    │ http://localhost:3001
│  * 只读模式访问    │
│    PostgreSQL      │
│  * 通过 RabbitMQ   │
│    发送写操作请求  │
└──────┬─────────────┘
       │ AMQP
       ▼
┌────────────────────┐
│   RabbitMQ         │ (消息队列)
│                    │
│  - base_data_queue │
│  - kline_data_queue│
└──────┬─────────────┘
       │ AMQP
       ▼
┌────────────────────┐
│  后台服务端        │ (Node.js + TypeScript)
│                    │
│  * 读写模式访问    │
│    PostgreSQL      │
│  * 消费队列消息    │
│  * 数据抓取        │
└────────────────────┘
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

### 前台服务端
- Node.js
- Express.js
- TypeScript
- pg (PostgreSQL 客户端)
- amqplib (RabbitMQ 客户端)

### 后台服务端
- Node.js
- TypeScript
- pg (PostgreSQL 客户端)
- amqplib (RabbitMQ 消费者)
- Python 脚本 (数据抓取)

### 数据抓取优化
- DuckDB (临时存储，用于批量导入)
- 先存入 DuckDB 快速写入，再批量导入 PostgreSQL

### 基础设施
- PostgreSQL (关系型数据库)
- RabbitMQ (消息队列)

## 安装和配置

### 前置要求

1. **Node.js 18+** 和 **pnpm**
2. **PostgreSQL** (默认配置: 127.0.0.1:5432, 数据库: ivydata, 用户: ivydata)
3. **RabbitMQ 服务** (默认配置: 127.0.0.1:5672, 用户/密码: rabbitmq/rabbitmq)
4. **通达信软件** (路径: D:\new_tdx64\tdxw.exe) - 仅后台服务端需要
5. **Python 3+** (数据抓取脚本需要)

### Python 依赖

```bash
pip install psycopg2-binary duckdb akshare pandas
```

### 安装依赖

```bash
pnpm install
```

## 启动服务

### 完整启动流程（推荐）

1. **确保 PostgreSQL 服务已启动**
2. **确保 RabbitMQ 服务已启动**
3. **确保通达信软件已启动**（仅后台服务端需要）
4. **启动后台服务端**：
   ```bash
   pnpm run backserver:dev
   ```
5. **启动前台服务端**：
   ```bash
   pnpm run frontserver:dev
   ```
6. **启动前端开发服务器**（带服务检查）：
   ```bash
   pnpm run client:dev:check
   ```

### 快速启动（不检查）

同时启动前端和前台服务端：
```bash
pnpm run dev
```

### 单独启动各服务

| 服务 | 命令 | 说明 |
|------|------|------|
| 前端 | `pnpm run client:dev` | http://localhost:5173 |
| 前台服务端 | `pnpm run frontserver:dev` | http://localhost:3001 |
| 后台服务端 | `pnpm run backserver:dev` | 无 HTTP 端口 |

## 目录结构

```
ivydata/
├── client/              # 前端源代码
│   ├── src/
│   │   ├── components/ # 组件
│   │   ├── pages/      # 页面
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── ...
├── server/              # 前台服务端
│   ├── src/
│   │   ├── routes/     # API 路由
│   │   ├── services/   # 服务模块
│   │   ├── db.ts       # 数据库连接
│   │   ├── config.ts   # 配置
│   │   └── index.ts    # 入口
│   └── package.json
├── worker/              # 后台服务端
│   ├── src/
│   │   ├── handlers/   # 消息处理器
│   │   ├── db.ts       # 数据库连接
│   │   ├── rabbitmq.ts # RabbitMQ 消费者
│   │   ├── config.ts   # 配置
│   │   └── index.ts    # 入口
│   └── package.json
├── data/                # Python 数据抓取脚本
│   ├── base_data_with_duckdb.py    # 基础数据抓取（使用 DuckDB 临时存储）
│   ├── day_k_data_with_duckdb.py   # K线数据抓取（使用 DuckDB 临时存储）
│   ├── check_and_fill_kline_data.py # K线数据检查和补充
│   └── ...
├── test/                # 测试文件
│   ├── check/           # 检查脚本
│   │   ├── check_postgres_connection.py  # PostgreSQL 连接检查
│   │   ├── check_all.py                  # 完整项目检查
│   │   ├── clear_postgres_tables.py      # 清空数据库表
│   │   └── ...
│   ├── base/            # 基础测试
│   └── tdx/             # 通达信测试
├── db/                  # DuckDB 临时数据库文件
│   └── temp_ivy.duckdb (临时使用)
├── package.json
├── POSTGRESQL_MIGRATION.md  # PostgreSQL 迁移指南
└── README.md
```

## API 接口

### 前台服务端 (http://localhost:3001)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/data/stats` | 获取统计数据 |
| GET | `/api/data/base-data` | 获取基础数据 |
| POST | `/api/data/base-data` | 抓取基础数据 |
| GET | `/api/data/kline-data` | 获取 K 线数据 |
| POST | `/api/data/kline-data` | 抓取 K 线数据 |
| GET | `/api/data/kline-data/check` | 检查 K 线数据完整性 |
| POST | `/api/data/kline-data/check` | 检查并补充 K 线数据 |

## 配置说明

### PostgreSQL 配置

**数据库信息**：
- 主机: `127.0.0.1`
- 端口: `5432`
- 数据库: `ivydata`
- 用户: `ivydata`
- 密码: `jcXz3rPjWrHY8MKF`

### RabbitMQ 配置

**前台服务端** (`server/src/config.ts`):
```typescript
export const RABBITMQ_CONFIG = {
  host: '127.0.0.1',
  port: 5672,
  username: 'rabbitmq',
  password: 'rabbitmq'
}
```

**后台服务端** (`worker/src/config.ts`):
```typescript
export const config = {
  rabbitmq: {
    url: 'amqp://rabbitmq:rabbitmq@127.0.0.1:5672'
  }
}
```

### 通达信软件路径

- 路径: `D:\new_tdx64\tdxw.exe`

### DuckDB 临时存储路径

- 临时数据库: `D:\dev\ai\ivydata\db\temp_ivy.duckdb`

## 数据抓取优化方案

### 为什么使用 DuckDB 临时存储？

1. **快速写入** - DuckDB 的写入性能远高于逐行插入 PostgreSQL
2. **批量导入** - 先收集所有数据，再一次性导入 PostgreSQL
3. **自动管理** - 脚本会自动创建、使用和删除临时数据库文件

### 数据流程

1. **检查临时数据库** - 如果存在则删除
2. **创建临时 DuckDB** - 创建新的临时数据库和表
3. **抓取数据** - 从数据源获取数据，快速写入 DuckDB
4. **批量导入** - 从 DuckDB 批量读取并导入 PostgreSQL
5. **清理** - 删除临时 DuckDB 文件

## 启动检查

服务启动时会自动进行以下检查：

### 后台服务端
1. ✅ 通达信软件是否已启动
2. ✅ RabbitMQ 是否可连接

### 前台服务端
1. ✅ RabbitMQ 是否可连接

### 前端 (使用 client:dev:check)
1. ✅ 前台服务端是否已启动

## 开发说明

### 数据库表结构

后台服务端首次启动时会自动创建以下表：

1. **base_data** - 基础数据（股票/基金列表）
2. **kline_data** - K 线数据
3. **grab_record** - 抓取记录

### 数据流程

1. **读操作**: 前端 → 前台服务端 → PostgreSQL
2. **写操作**: 前端 → 前台服务端 → RabbitMQ → 后台服务端 → PostgreSQL

### 队列名称

- `base_data_queue`: 基础数据抓取任务
- `kline_data_queue`: K 线数据抓取任务

### K 线数据完整性检查

Dashboard 页面提供以下功能：
1. **检查完整性** - 查看每个代码的 K 线数据是否完整
2. **检查并补充** - 自动检查并补充缺失的 K 线数据
3. **指定代码检查** - 可指定单个代码进行检查

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

## 文档结构

项目文档组织如下：

```
ivydata/
├── README.md                      # 本文档 - 项目概览和使用说明
└── docs/                          # 详细文档目录
    ├── PRD.md                     # 产品需求文档
    ├── POSTGRESQL_MIGRATION.md   # PostgreSQL 迁移指南
    └── archive/                   # 历史文档（归档）
        └── tech_architecture_duckdb.md  # 旧版技术架构（DuckDB）
```

## 故障排除

详细的故障排除指南请参考 [docs/POSTGRESQL_MIGRATION.md](./docs/POSTGRESQL_MIGRATION.md)
