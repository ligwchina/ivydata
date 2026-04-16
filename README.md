# IvyData - 股票数据分析系统

一个基于 React + TypeScript + PostgreSQL + RabbitMQ 的股票数据分析系统。

## 快速开始

### 前置要求

1. **Node.js 18+** 和 **pnpm**
2. **PostgreSQL** (127.0.0.1:5432, 数据库: ivydata, 用户: ivydata)
3. **RabbitMQ 服务** (127.0.0.1:5672, 用户/密码: rabbitmq/rabbitmq)
4. **通达信软件** (D:\new_tdx64\tdxw.exe) - 仅后台服务端需要
5. **Python 3+**

### 安装

```bash
pip install psycopg2-binary duckdb akshare pandas
pnpm install
```

### 启动

```bash
# 1. 启动后台服务端
pnpm run backserver:dev

# 2. 启动前台服务端
pnpm run frontserver:dev

# 3. 启动前端
pnpm run client:dev
```

访问 http://localhost:5173

## 文档

详细文档请查看 [docs/](./docs/) 目录：

- [docs/GUIDE.md](./docs/GUIDE.md) - 完整项目指南
- [docs/PRD.md](./docs/PRD.md) - 产品需求文档
- [docs/POSTGRESQL_MIGRATION.md](./docs/POSTGRESQL_MIGRATION.md) - 迁移指南
