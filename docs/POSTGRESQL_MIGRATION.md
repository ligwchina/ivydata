# PostgreSQL 数据库迁移指南

## 概述

本项目已从 DuckDB 迁移到 PostgreSQL，以实现更好的并发访问和数据管理。

## 数据库配置

PostgreSQL 配置信息：
- 主机: 127.0.0.1
- 端口: 5432
- 数据库: ivydata
- 用户: ivydata
- 密码: jcXz3rPjWrHY8MKF

## 迁移内容

### 1. Node.js 服务端

#### 前台服务端 (server/)
- `package.json`: 移除 duckdb，添加 pg
- `src/db.ts`: PostgreSQL 连接池模块
- `src/routes/data.ts`: 使用 PostgreSQL 参数格式 ($1, $2, ...)

#### 后台服务端 (worker/)
- `package.json`: 移除 duckdb，添加 pg
- `src/db.ts`: PostgreSQL 连接池模块
- `src/index.ts`: 检查表存在性，创建表结构

### 2. Python 数据抓取脚本

#### 基础数据抓取 (data/base_data.py)
- 使用 psycopg2 连接 PostgreSQL
- 使用 execute_values 批量插入优化性能
- 使用 PostgreSQL 语法（SERIAL, %s 占位符）

#### K线数据抓取 (data/day_k_data.py)
- 使用 psycopg2 连接 PostgreSQL
- 使用 execute_values 批量插入优化性能
- 使用 ON CONFLICT 处理唯一约束冲突

### 3. 检查脚本

- `test/check/check_postgres_connection.py`: PostgreSQL 连接检查
- `test/check/check_all.py`: 完整项目检查

## 安装依赖

### Node.js 依赖

```bash
# 前台服务端
cd server
pnpm install

# 后台服务端
cd ../worker
pnpm install
```

### Python 依赖

```bash
pip install psycopg2-binary
```

## PostgreSQL 数据库准备

### 1. 确保 PostgreSQL 服务已启动

```bash
# Windows
# 使用服务管理器启动 PostgreSQL 服务

# 或使用命令行
net start postgresql-x64-16  # 根据你的版本调整
```

### 2. 创建数据库和用户（如果尚未创建）

```sql
-- 以 postgres 用户登录
psql -U postgres

-- 创建数据库
CREATE DATABASE ivydata;

-- 创建用户
CREATE USER ivydata WITH PASSWORD 'jcXz3rPjWrHY8MKF';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE ivydata TO ivydata;

-- 连接到新数据库
\c ivydata

-- 授权表权限
GRANT ALL ON SCHEMA public TO ivydata;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ivydata;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ivydata;
```

## 运行检查

```bash
cd test/check

# 检查 PostgreSQL 连接
python check_postgres_connection.py

# 完整检查
python check_all.py
```

## 启动服务

### 1. 启动后台服务端

```bash
pnpm run backserver:dev
```

后台服务端会自动创建所需的表结构。

### 2. 启动前台服务端

```bash
pnpm run frontserver:dev
```

### 3. 启动前端

```bash
pnpm run client:dev
```

## 数据库表结构

### base_data 表

```sql
CREATE TABLE base_data (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    code_converted VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    stock_or_fund INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### kline_data 表

```sql
CREATE TABLE kline_data (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open NUMERIC(18, 4) NOT NULL,
    high NUMERIC(18, 4) NOT NULL,
    low NUMERIC(18, 4) NOT NULL,
    close NUMERIC(18, 4) NOT NULL,
    volume BIGINT NOT NULL,
    amount NUMERIC(18, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, date)
);
```

### grab_record 表

```sql
CREATE TABLE grab_record (
    code VARCHAR(20) PRIMARY KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP
);
```

## 索引

```sql
CREATE INDEX idx_kline_code ON kline_data(code);
CREATE INDEX idx_kline_date ON kline_data(date);
```

## PostgreSQL 优势

相比 DuckDB，PostgreSQL 提供：

1. **真正的并发访问**：多个客户端可以同时读写
2. **成熟的客户端-服务器架构**：更好的网络访问支持
3. **完善的事务支持**：ACID 兼容
4. **丰富的生态系统**：更多工具和库支持
5. **更好的安全性**：用户权限管理

## 故障排除

### 连接失败

如果遇到连接失败：

1. 确认 PostgreSQL 服务已启动
2. 检查防火墙设置
3. 验证用户名和密码
4. 确认数据库存在

### 权限错误

如果遇到权限错误：

```sql
-- 以 postgres 用户登录
psql -U postgres -d ivydata

-- 重新授权
GRANT ALL ON SCHEMA public TO ivydata;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ivydata;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ivydata;
```

## 回滚到 DuckDB

如果需要回滚到 DuckDB，请查看 git 历史记录恢复相关文件。
