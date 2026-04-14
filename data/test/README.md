# Data 目录开发文档

## 目录结构

```
data/
├── code_converter.py   # 代码转换工具
├── base_data.py        # 基础数据初始化
├── day_k_data.py       # K线数据抓取
├── config.txt         # 配置文件
└── README.md          # 开发文档
```

## 依赖

- Python 3.11+
- duckdb
- pandas
- akshare
- requests

通达信软件（Tushare pro 授权）

## 数据库

### 数据库文件
- `db/ivy.duckdb`

### 表结构

#### t_base - 基础代码表

| 字段 | 类型 | 说明 |
|------|------|------|
| code | VARCHAR | 原始代码（主键） |
| name | VARCHAR | 名称 |
| code_converted | VARCHAR | 带后缀代码 |
| exchange | VARCHAR | 交易所（SH/SZ/BJ） |
| stock_or_fund | INTEGER | 1=股票，2=基金 |

#### t_day_k - K线数据表

| 字段 | 类型 | 说明 |
|------|------|------|
| code | VARCHAR | 代码（主键） |
| date | DATE | 日期（主键） |
| open | DOUBLE | 开盘价 |
| high | DOUBLE | 最高价 |
| low | DOUBLE | 最低价 |
| close | DOUBLE | 收盘价 |
| volume | DOUBLE | 成交量 |
| amount | DOUBLE | 成交额 |

#### t_grab_record - 抓取记录表

| 字段 | 类型 | 说明 |
|------|------|------|
| code | VARCHAR | 代码（主键） |
| start_time | TIMESTAMP | 开始时间 |
| end_time | TIMESTAMP | 结束时间 |

---

## 文件说明

### 1. code_converter.py

股票和基金代码转换工具模块。

#### 函数

- `convert_code(code)` - 将代码转换为带后缀格式
  - 参数: code (str/int) - 原始代码，如 "600519"
  - 返回: 带后缀代码，如 "600519.SH"

- `convert_batch(code_list)` - 批量转换代码列表

- `get_exchange(code)` - 获取交易所标识
  - 返回: SH/SZ/BJ/未知

- `is_a_stock(code)` - 判断是否为A股股票

- `is_fund(code)` - 判断是否为基金代码

- `remove_suffix(code)` - 移除代码后缀

#### 代码前缀规则

| 前缀 | 类型 | 交易所 |
|------|------|--------|
| 15/16/18 | 基金 | SZ |
| 50/51/52/53/55/56/58 | 基金 | SH |
| 6 | 股票 | SH |
| 0/3 | 股票 | SZ |
| 48 | 股票 | BJ |
| 9 | B股 | SH |
| 2 | B股 | SZ |

---

### 2. base_data.py

基础数据初始化脚本，用于初始化 t_base 表。

#### 功能

1. 获取沪深京三地全部A股列表（使用 akshare）
2. 获取天天基金网场内交易基金列表（网页抓取）
3. 将数据存入 t_base 表

#### 使用方法

```bash
python base_data.py
```

#### 输出示例

```
开始初始化基础数据...
数据库和表创建完成
成功获取5491只股票列表
成功插入5491条股票数据
成功获取1438只基金列表
成功插入1438条基金数据
表中总数据量: 6929
股票数量: 5491, 基金数量: 1438
数据初始化完成!
```

---

### 3. day_k_data.py

K线数据抓取脚本，从通达信获取每日K线数据。

#### 功能

1. 读取配置文件 `config.txt` 中的 `is_run` 值
2. 根据 t_base 和 t_grab_record 表确定需要抓取的代码
3. 从通达信获取日K线数据
4. 保存到 t_day_k 表
5. 更新 t_grab_record 表记录抓取时间

#### 配置文件 (config.txt)

```
is_run=0
```

- `is_run=0`: 抓取完当前代码后停止
- `is_run=1`: 循环继续抓取下一条编码的K线数据

#### 使用方法

```bash
python day_k_data.py
```

#### 工作流程

```
1. 读取 config.txt 中的 is_run 配置
2. 查询 t_base 和 t_grab_record 获取待抓取代码
3. 循环遍历每个代码:
   - 记录开始时间
   - 调用通达信接口获取K线数据
   - 保存到 t_day_k 表
   - 记录结束时间到 t_grab_record
   - 如果 is_run=0 则停止，否则继续
```

#### 通达信配置

默认路径: `D:\new_tdx64`

如需修改，编辑 `day_k_data.py` 第7行:

```python
tdx_install_path = r"D:\new_tdx64"
```

---

## 数据统计

- 股票数量: 5491
- 基金数量: 1438
- 总计: 6929

---

## 常见问题

### Q: 如何重新抓取某个代码的K线数据？

A: 从 t_grab_record 表中删除该代码的记录:

```sql
DELETE FROM t_grab_record WHERE code = '600519';
```

然后重新运行 day_k_data.py

### Q: 如何查看抓取进度？

A: 查询 t_grab_record 表:

```sql
SELECT * FROM t_grab_record ORDER BY end_time DESC LIMIT 10;
```

### Q: 如何查看K线数据？

A: 查询 t_day_k 表:

```sql
SELECT * FROM t_day_k WHERE code = '513050' ORDER BY date DESC LIMIT 10;
```
