# AI智慧养殖系统V2.0 - 后端API

> 模块化单体架构 (Modular Monolith) | FastAPI + SQLAlchemy + MySQL 8.0

## 项目概述

本项目为AI智慧养殖系统V2.0的后端API服务，覆盖8个P0核心模块：

| 模块 | 功能 | 端点前缀 |
|------|------|---------|
| 批次全生命周期 | 批次详情、关联数据聚合、死淘分析、出栏计划 | `/api/v2/batches` |
| 个体生长曲线 | 个体体重查询、批次生长聚合、标准曲线对比 | `/api/v2/individuals` |
| 性能偏差看板 | 成活率/日增重/料肉比偏差计算 | `/api/v2/performance` |
| 中试效果对比 | 实验组vs对照组指标对比、项目进度 | `/api/v2/pilots` |
| 财务收支管理 | 收支CRUD、月度趋势、科目占比、批次归集 | `/api/v2/financial-transactions` |
| 批次利润分析 | 利润计算、排名、单只成本/收入/利润 | `/api/v2/profit` |
| 溯源查询 | 溯源码查询、全链路时间线 | `/api/v2/traceability` |
| 库存管理 | 库存CRUD、预警查询、出入库流水 | `/api/v2/inventory` |
| 系统配置 | 三级作用域配置管理 | `/api/v2/config` |

## 快速开始

### 1. 环境准备

- Python 3.11+
- MySQL 8.0
- Docker & Docker Compose（可选）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置数据库连接信息
```

### 4. 初始化数据库

```bash
python scripts/init_db.py
```

参数说明：
- `--drop`：先删除所有表再重新创建
- `--skip-seed`：跳过种子数据初始化

### 5. 启动服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## Docker 部署

### 使用 Docker Compose（推荐）

```bash
# 一键启动 MySQL + API
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 初始化数据库
docker-compose exec api python scripts/init_db.py
```

### 使用 Dockerfile

```bash
# 构建镜像
docker build -t ai-breeding-api:v2.0 .

# 运行容器
docker run -d -p 8000:8000 \
  -e DB_HOST=your_mysql_host \
  -e DB_PASSWORD=your_password \
  ai-breeding-api:v2.0
```

## 项目结构

```
ai_breeding_v2/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理 (pydantic-settings)
│   ├── database.py          # SQLAlchemy 引擎与会话
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py          # 30张表的ORM模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── common.py        # 通用响应Schema
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── batches.py       # 批次管理
│   │   ├── growth.py        # 生长曲线
│   │   ├── performance.py   # 性能偏差
│   │   ├── pilot.py         # 中试管理
│   │   ├── finance.py       # 财务收支
│   │   ├── profit.py        # 利润分析
│   │   ├── traceability.py  # 溯源查询
│   │   ├── inventory.py     # 库存管理
│   │   └── config.py        # 系统配置
│   └── utils/
│       └── response.py      # 统一响应格式
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures
│   └── test_api.py          # API测试用例（11个测试类）
├── scripts/
│   └── init_db.py           # 数据库初始化脚本
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## API 规范

### 统一响应格式

**成功响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**分页响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

**错误响应：**
```json
{
  "code": 404,
  "message": "批次不存在",
  "detail": "可选的详细错误信息"
}
```

### 通用查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `page` | int | 页码，默认1，最小1 |
| `page_size` | int | 每页条数，默认20，最大100 |
| `keyword` | string | 关键字搜索 |
| `start_date` | date | 开始日期 |
| `end_date` | date | 结束日期 |

### 主要端点速查

```
# 批次管理
GET    /api/v2/batches                    # 批次列表
GET    /api/v2/batches/{id}               # 批次详情
GET    /api/v2/batches/{id}/lifecycle     # 生命周期聚合
GET    /api/v2/batches/{id}/growth-summary # 生长汇总
GET    /api/v2/batches/{id}/performance   # 性能偏差
GET    /api/v2/batches/{id}/profit        # 利润分析

# 生长曲线
GET    /api/v2/individuals/{id}/growth-curve    # 个体生长曲线
GET    /api/v2/individuals/{id}/growth-records  # 生长记录
GET    /api/v2/individuals/{id}/pedigree        # 谱系

# 性能偏差
GET    /api/v2/performance/dashboard      # 性能看板
GET    /api/v2/performance/deviation      # 偏差列表
GET    /api/v2/performance/benchmark      # 标准对比

# 中试管理
GET    /api/v2/pilots                     # 中试项目列表
GET    /api/v2/pilots/{id}                # 中试详情
GET    /api/v2/pilots/{id}/comparison     # 实验组vs对照组对比

# 财务收支
GET    /api/v2/financial-transactions     # 收支列表
POST   /api/v2/financial-transactions     # 创建收支
GET    /api/v2/financial-transactions/summary  # 收支汇总

# 利润分析
GET    /api/v2/profit/ranking             # 利润排名
GET    /api/v2/profit/trend               # 利润趋势

# 溯源查询
GET    /api/v2/traceability/{code}        # 溯源码查询
GET    /api/v2/traceability/completeness  # 溯源完整度

# 库存管理
GET    /api/v2/inventory                  # 库存列表
POST   /api/v2/inventory                  # 创建库存
POST   /api/v2/inventory/{id}/transactions # 出入库
GET    /api/v2/inventory/alerts           # 库存预警

# 系统配置
GET    /api/v2/config                     # 配置列表
POST   /api/v2/config                     # 创建配置
PUT    /api/v2/config/{id}                # 更新配置
GET    /api/v2/config/{id}/history        # 配置历史
```

## 系统配置（三级作用域）

`sys_config` 表支持三级作用域读取：

| scope_type | 含义 | scope_id |
|-----------|------|---------|
| 1 | 全局 | 0 |
| 2 | 鸡舍级 | house_id |
| 3 | 批次级 | batch_id |

读取优先级：**批次级 > 鸡舍级 > 全局**，未找到时使用全局默认值。

### 预置配置项

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `trace_mode` | `ear_tag` | 追踪模式：`ear_tag`=耳标扫码, `sampling`=批次抽样 |
| `sampling_rate` | `10` | 批次抽样比例（%） |
| `auto_finance_link` | `0` | 财务自动联动：0=手动, 1=自动 |
| `traceability_print` | `0` | 溯源码打印：0=仅系统内, 1=支持物理打印 |
| `pilot_stat_method` | `mean_compare` | 中试统计：`mean_compare`=均值对比, `t_test`=t检验 |
| `alert_low_stock` | `1` | 库存低量预警开关 |
| `alert_expiry` | `1` | 临期预警开关 |
| `expiry_warning_days` | `30` | 临期预警天数 |

## 测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定模块测试

```bash
pytest tests/test_api.py::TestBatches -v
pytest tests/test_api.py::TestFinance -v
pytest tests/test_api.py::TestInventory -v
```

### 测试覆盖

- 11个测试类，覆盖全部8个P0模块 + 系统配置 + 通用响应格式 + 边界条件
- 使用SQLite内存数据库，无需MySQL即可运行
- 包含：空数据、有数据、筛选、分页、创建、更新、错误处理、边界条件

## 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.115.0 | Web框架 |
| SQLAlchemy | 2.0.35 | ORM |
| PyMySQL | 1.1.1 | MySQL驱动 |
| Pydantic | 2.9.2 | 数据校验 |
| pydantic-settings | 2.5.2 | 配置管理 |
| Uvicorn | 0.30.0 | ASGI服务器 |
| pytest | 8.3.3 | 测试框架 |
| httpx | 0.27.2 | HTTP客户端（测试用） |
| Alembic | 1.13.3 | 数据库迁移 |

## 数据库设计

共30张表，覆盖12个业务域：

- **基础数据**：breed, house
- **个体管理**：batch, animal_individual, growth_record, health_record
- **进销存**：purchase_order, purchase_item, inventory, inventory_transaction, hatching_record, sales_order, sales_item, culling_record
- **养殖操作**：breeding_operation, environment_param, alert, feed_consumption
- **对比分析**：benchmark_standard, performance_analysis
- **溯源管理**：traceability_chain
- **中试管理**：pilot_project, pilot_batch, pilot_indicator
- **行情数据**：market_price
- **系统配置**：sys_config, sys_config_history
- **财务管理**：financial_transaction, cost_allocation, profit_analysis

## 工作假设

1. **个体追踪模式**：优先耳标扫码模式，批次抽样模式（10%）作为降级，通过 `trace_mode` 配置切换
2. **财务自动联动**：本期仅支持手动录入，`auto_finance_link` 默认为关闭
3. **溯源码打印**：本期仅实现系统内二维码生成和Web查询，`traceability_print` 默认关闭
4. **中试统计**：本期仅做实验组vs对照组均值对比，`pilot_stat_method` 默认为 `mean_compare`

## 许可证

内部项目 - 深圳合润供应链科技有限公司
