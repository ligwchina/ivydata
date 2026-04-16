# IvyData - 股票数据分析系统

一个基于 React + TypeScript + PostgreSQL 的股票数据分析系统。

## 快速开始

### 前置要求

1. **Node.js 18+** 和 **pnpm**
2. **PostgreSQL** (127.0.0.1:5432, 数据库: ivydata, 用户: ivydata)
3. **通达信软件** (D:\new_tdx64\tdxw.exe) - 数据抓取需要
4. **Python 3+** (推荐使用 myenv311 环境)

### 安装

```bash
# 激活 Python 环境（推荐）
conda activate myenv311

# 安装 Python 依赖
pip install psycopg2-binary akshare pandas duckdb

# 安装 Node 依赖
pnpm install
```

### 启动

```bash
# 1. 启动服务端
pnpm run server:dev

# 2. 启动前端
pnpm run client:dev
```

访问 http://localhost:5173

## 数据抓取

数据抓取需要手动运行 Python 脚本：

```bash
# 激活 Python 环境
conda activate myenv311

# 1. 抓取基础数据（股票/基金列表）
python data/base_data.py

# 2. 抓取K线数据
python data/day_k_data.py

# 3. 检查并补充K线数据（可选）
python data/check_and_fill_kline_data.py
```

## 数据库

### 表结构

- **base_data**: 股票/基金基础数据
- **kline_data**: K线数据（OHLCV）
- **grab_record**: 抓取记录
- **sys_options**: 系统配置（如 last_base_data_fetch, last_kline_data_fetch）

### 数据库初始化

- 服务端启动时会自动检查并创建表
- Python 脚本使用 db_helper.py 管理表创建和 sys_options 更新

## 文档

详细文档请查看 [docs/](./docs/) 目录：

- [docs/GUIDE.md](./docs/GUIDE.md) - 完整项目指南
- [docs/PRD.md](./docs/PRD.md) - 产品需求文档
