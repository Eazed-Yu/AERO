# AERO 建筑能源智能管理系统 - 技术设计文档

## 1. 系统架构概述

AERO（建筑能源智能管理系统）采用**前后端分离**架构，后端基于 **FastAPI**（Python 异步框架），前端基于 **Vue 3** 组合式 API，两者通过 RESTful API 进行通信。

整体架构分为六层：

| 层级 | 名称 | 技术栈 |
|------|------|--------|
| 用户层 | Web 浏览器 | 现代浏览器 |
| 前端层 | SPA 应用 | Vue 3 + Naive UI + ECharts |
| API 层 | RESTful 接口 | FastAPI（`/api/v1/*`） |
| 业务逻辑层 | 服务模块 | Services（建筑、能耗、统计、异常、导出、问答） |
| 组件层 | 内部组件 | LightRAG、ThresholdDetector、ExportService |
| 数据层 | 持久化 | PostgreSQL + LightRAG Storage |

核心设计原则：

- **异步优先**：后端全链路基于 `async/await`，使用 `asyncpg` 异步驱动
- **分层解耦**：models / schemas / services / routers 四层分离
- **策略可扩展**：异常检测采用策略模式，支持阈值检测与 ML 检测的无缝切换
- **RAG 可选**：LightRAG 作为可选组件，不可用时系统降级运行（仅禁用问答功能）

---

## 2. 技术选型说明

### 2.1 后端技术栈

| 组件 | 技术选型 | 版本要求 | 选型理由 |
|------|----------|----------|----------|
| Web 框架 | FastAPI | >= 0.115 | 原生异步、自动生成 OpenAPI 文档、类型校验、高性能 |
| ASGI 服务器 | Uvicorn | >= 0.30 | 轻量级、支持 HTTP/1.1 和 WebSocket、热重载 |
| ORM | SQLAlchemy 2.0 | >= 2.0 | 异步支持（asyncio extension）、声明式模型、成熟生态 |
| 异步 PG 驱动 | asyncpg | >= 0.29 | PostgreSQL 专用异步驱动，性能优于通用方案 |
| 数据库迁移 | Alembic | >= 1.13 | SQLAlchemy 官方迁移工具，支持自动生成迁移脚本 |
| 数据校验 | Pydantic v2 | >= 2.0 (via pydantic-settings) | FastAPI 原生集成，高性能的数据序列化/反序列化 |
| 数据处理 | Pandas + NumPy | >= 2.0 / >= 1.24 | ETL 数据转换、统计计算，科学计算事实标准 |
| Excel 导出 | openpyxl | >= 3.1 | 纯 Python 实现 xlsx 读写，无需系统依赖 |
| RAG 引擎 | LightRAG (lightrag-hku) | >= 1.4.9 | 轻量级 RAG 框架，支持知识图谱增强检索 |
| LLM 接口 | OpenAI 兼容 API | - | 通过 SiliconFlow 调用 Qwen2.5-7B-Instruct |
| Embedding | BAAI/bge-m3 | - | 多语言嵌入模型，1024 维向量，适合中文场景 |
| MCP 协议 | FastMCP | 可选 | Model Context Protocol 工具定义，为 AI Agent 暴露接口 |

### 2.2 前端技术栈

| 组件 | 技术选型 | 版本要求 | 选型理由 |
|------|----------|----------|----------|
| 框架 | Vue 3 | >= 3.5 | 组合式 API、Proxy 响应式、TypeScript 友好 |
| 构建工具 | Vite 6 | >= 6.0 | ESM 原生开发服务器、极速 HMR、Rollup 生产构建 |
| UI 组件库 | Naive UI | >= 2.40 | Vue 3 原生、TypeScript 编写、主题定制灵活 |
| 图表库 | ECharts + vue-echarts | >= 5.5 / >= 7.0 | 丰富图表类型、大数据量渲染、良好的 Vue 集成 |
| 状态管理 | Pinia | >= 2.2 | Vue 3 官方推荐、组合式 API 风格、DevTools 支持 |
| 路由 | Vue Router | >= 4.4 | Vue 3 官方路由方案 |
| HTTP 客户端 | Axios | >= 1.7 | 拦截器机制、请求/响应转换、取消请求支持 |
| 类型检查 | TypeScript | ~5.6 | 类型安全、编译时错误检查 |
| 图标 | @vicons/ionicons5 | >= 0.12 | Naive UI 推荐图标集 |

### 2.3 数据层

| 组件 | 技术选型 | 选型理由 |
|------|----------|----------|
| 关系数据库 | PostgreSQL | 强大的 JSON 支持、时间序列查询性能好、CHECK 约束完善 |
| RAG 存储 | LightRAG 内置存储 | JSON KV + NanoVectorDB + NetworkX 图存储，开箱即用 |

---

## 3. 数据流程设计

### 3.1 数据导入流程

```
公开数据集 (CSV/JSON)
    │
    ▼
AbstractETLAdapter（extract → transform → load）
    │
    ├─ extract(): 从文件/URL 读取原始数据 → pd.DataFrame
    ├─ transform(): 转换为 AERO 标准格式 → list[dict]
    └─ load(): 批量写入数据库 → int (记录数)
    │
    ▼
ImportService（bulk_import_energy）
    │
    ├─ JSON 批量导入（POST /api/v1/import/energy）
    └─ 文件上传导入（POST /api/v1/import/upload，支持 .json/.csv）
    │
    ▼
PostgreSQL (energy_records 表)
```

数据校验由 Pydantic Schema（`EnergyRecordCreate`）在导入时执行，校验失败的行记入 `error_details` 返回给前端。

### 3.2 查询统计流程

```
用户在前端设置筛选条件
    │
    ├─ building_id, start_time, end_time
    ├─ metrics（可选，逗号分隔）
    └─ 分页参数（page, page_size, sort_by, sort_order）
    │
    ▼
Axios → GET /api/v1/energy?building_id=...&start_time=...
    │
    ▼
EnergyService.query(params: EnergyQueryParams)
    │
    ├─ 构建 SQLAlchemy 动态查询（where, order_by, limit/offset）
    └─ 返回 PaginatedResponse（items + total + page_info）
    │
    ▼
前端 ECharts 组件渲染（EnergyTrendChart / EnergyDistributionChart）
```

### 3.3 异常检测流程

```
能耗记录（energy_records）
    │
    ▼
AnomalyService.detect_anomalies(building_id, start_time, end_time)
    │
    ├─ 1. 从数据库查询时间范围内的 energy_records
    ├─ 2. 构造 DetectionContext（building_id + 阈值参数）
    └─ 3. 调用 AbstractDetector.detect(records, context)
         │
         ├─ ThresholdDetector（默认策略）
         │   ├─ 电力尖峰检测：electricity_kwh > mean × spike_factor
         │   ├─ COP 异常检测：COP < min_cop
         │   └─ 温度偏差检测：|supply_temp - expected| > deviation
         │
         └─ MLDetector（预留，尚未实现）
    │
    ▼
anomaly_events 表（持久化异常事件）
    │
    ▼
前端 AnomalyScatterChart 散点图可视化
```

### 3.4 智能问答流程

```
用户在前端提交问题
    │
    ▼
POST /api/v1/qa/query { question, mode }
    │
    ▼
QAService.ask(question, mode)
    │
    ▼
LightRAGService.query(question, mode)
    │
    ├─ mode = "local"：局部实体/关系检索
    ├─ mode = "global"：跨文档知识图谱检索
    ├─ mode = "hybrid"：混合检索（推荐）
    └─ mode = "naive"：朴素向量相似度检索
    │
    ▼
LightRAG 内部流程:
    ├─ Embedding（BAAI/bge-m3）→ 向量检索
    ├─ NetworkX 图存储 → 知识图谱遍历
    └─ LLM（Qwen2.5-7B-Instruct via SiliconFlow）→ 生成回答
    │
    ▼
QAQueryResponse { answer, mode, sources } → 前端展示
```

---

## 4. 模块架构设计

### 4.1 后端分层架构

```
backend/app/
├── models/          ← 数据模型层（SQLAlchemy ORM）
│   ├── base.py          TimestampMixin, generate_uuid
│   ├── building.py      Building 模型
│   ├── energy_record.py EnergyRecord 模型
│   ├── equipment.py     Equipment + EquipmentStatus 模型
│   └── anomaly.py       AnomalyEvent 模型
│
├── schemas/         ← 数据传输层（Pydantic v2 Schema）
│   ├── building.py      BuildingCreate / BuildingUpdate / BuildingResponse
│   ├── energy.py        EnergyRecordCreate / EnergyRecordResponse / EnergyImportRequest / ImportResult
│   ├── equipment.py     EquipmentResponse / EquipmentStatusResponse
│   ├── anomaly.py       AnomalyDetectRequest / AnomalyEventResponse
│   ├── statistics.py    AggregationResult / COPResult / AnomalyStatistics
│   ├── query.py         EnergyQueryParams / PaginatedResponse
│   └── report.py        QAQueryRequest / QAQueryResponse / QAIngestRequest
│
├── services/        ← 业务逻辑层
│   ├── building_service.py     建筑 CRUD
│   ├── energy_service.py       能耗查询（动态条件 + 分页）
│   ├── import_service.py       数据导入（批量插入 + 冲突处理）
│   ├── statistics_service.py   统计聚合 + COP 计算
│   ├── anomaly_service.py      异常检测编排
│   ├── equipment_service.py    设备管理
│   ├── export_service.py       CSV / Excel 导出
│   └── qa_service.py           RAG 问答编排
│
├── routers/         ← 路由控制层（FastAPI Router）
│   ├── buildings.py     /api/v1/buildings
│   ├── energy.py        /api/v1/energy
│   ├── data_import.py   /api/v1/import
│   ├── statistics.py    /api/v1/statistics
│   ├── anomaly.py       /api/v1/anomaly
│   ├── equipment.py     /api/v1/equipment
│   ├── export.py        /api/v1/export
│   └── qa.py            /api/v1/qa
│
├── detection/       ← 异常检测模块（策略模式）
├── rag/             ← RAG 模块
├── etl/             ← ETL 适配器
├── mcp/             ← MCP 协议
├── utils/           ← 工具函数
├── config.py        ← 配置管理
├── database.py      ← 数据库连接
└── main.py          ← 应用入口
```

调用链路：`Router → Service → Model/Schema`，Router 不直接操作数据库，所有业务逻辑集中在 Service 层。

### 4.2 异常检测：策略模式

```
AbstractDetector (ABC)
    │
    ├── detect(records, context) → list[dict]   ← 抽象方法
    │
    ├── ThresholdDetector（已实现）
    │   ├── 电力尖峰检测：值 > 均值 × spike_factor
    │   ├── COP 低值检测：COP < min_cop (默认 2.0)
    │   └── 温度偏差检测：|实际 - 期望| > deviation (默认 5°C)
    │
    └── MLDetector（预留接口）
        └── 将集成时间序列异常检测模型

DetectionContext:
    ├── building_id: str       ← 建筑标识
    └── thresholds: dict       ← 可覆盖的阈值参数
```

`AnomalyService` 负责编排：查询数据 → 构造上下文 → 调用检测器 → 持久化结果。切换检测策略仅需替换 `AbstractDetector` 实例，无需修改上层代码。

### 4.3 LightRAG 封装

`LightRAGService` 作为应用内部组件封装 LightRAG，而非独立微服务：

```
LightRAGService
    ├── initialize()         ← 应用启动时在 lifespan 中调用
    │   ├── 配置 LLM（SiliconFlow OpenAI 兼容接口）
    │   ├── 配置 Embedding（BAAI/bge-m3, 1024维）
    │   └── 初始化存储后端（JsonKV + NanoVectorDB + NetworkX）
    │
    ├── insert_document(text) ← 知识库灌入
    ├── query(question, mode) ← 四种检索模式
    ├── shutdown()            ← 应用关闭时清理
    └── is_available          ← 健康状态属性
```

降级策略：若 `lightrag-hku` 未安装或初始化失败，`is_available` 返回 `False`，QA 路由返回 503，其他功能不受影响。

### 4.4 ETL 接口

```
AbstractETLAdapter (ABC)
    ├── extract(source: str) → pd.DataFrame     ← 数据抽取
    ├── transform(raw: DataFrame) → list[dict]   ← 格式转换
    ├── load(records, db: AsyncSession) → int     ← 数据加载
    └── run(source, db) → int                     ← 完整 ETL 管道

计划适配的公开数据集:
    ├── University of Michigan Campus Dataset
    ├── AlphaBuilding Synthetic Dataset
    └── Building Data Genome Project 2
```

每个数据集实现一个具体的 Adapter 子类，将特定格式映射到 AERO 标准 Schema。

### 4.5 MCP 协议

通过 `FastMCP` 定义工具函数，为 AI Agent 暴露接口：

```
FastMCP("AERO Energy Management")
    ├── query_energy_data()       ← 查询能耗数据
    ├── calculate_cop()           ← 计算 COP
    ├── detect_anomalies()        ← 运行异常检测
    └── get_building_statistics() ← 获取建筑统计
```

MCP 工具为可选功能，`FastMCP` 未安装时自动跳过注册。

---

## 5. 接口设计

### REST API 概览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **建筑管理** | GET | `/api/v1/buildings` | 建筑列表（支持 building_type 筛选） |
| | GET | `/api/v1/buildings/{building_id}` | 建筑详情 |
| | POST | `/api/v1/buildings` | 创建建筑 |
| | PUT | `/api/v1/buildings/{building_id}` | 更新建筑 |
| **能耗查询** | GET | `/api/v1/energy` | 能耗记录查询（分页 + 多条件筛选） |
| **数据导入** | POST | `/api/v1/import/energy` | JSON 批量导入 |
| | POST | `/api/v1/import/upload` | 文件上传导入（JSON/CSV） |
| **统计分析** | GET | `/api/v1/statistics/aggregate` | 按时间周期聚合（hour/day/week/month） |
| | GET | `/api/v1/statistics/cop` | COP 计算（按时间周期） |
| | GET | `/api/v1/statistics/anomaly-summary` | 异常统计汇总 |
| **异常检测** | GET | `/api/v1/anomaly` | 异常事件列表（支持多维筛选） |
| | POST | `/api/v1/anomaly/detect` | 触发异常检测 |
| | PATCH | `/api/v1/anomaly/{anomaly_id}/resolve` | 标记异常已解决 |
| **设备管理** | GET | `/api/v1/equipment` | 设备列表 |
| | GET | `/api/v1/equipment/{device_id}` | 设备详情 + 最新状态 |
| | GET | `/api/v1/equipment/{device_id}/status-history` | 设备状态历史 |
| **数据导出** | POST | `/api/v1/export/csv` | 导出 CSV |
| | POST | `/api/v1/export/excel` | 导出 Excel |
| **智能问答** | POST | `/api/v1/qa/query` | 提交问题 |
| | POST | `/api/v1/qa/ingest` | 灌入知识文档 |
| | GET | `/api/v1/qa/modes` | 检索模式列表 |
| **健康检查** | GET | `/api/health` | 系统健康状态 |

---

## 6. COP 计算算法

### 6.1 计算公式

COP（Coefficient of Performance，性能系数）用于评估 HVAC 系统的制冷/制热效率。

**制冷量计算：**

```
Q_cooling = flow_rate_m3h × 1.163 × |return_temp - supply_temp|  [kW]
```

推导过程：
- 水的比热容：`c = 4.186 kJ/(kg·°C)`
- 水的密度：`ρ ≈ 1000 kg/m³`
- 流量单位转换：`flow_rate_m3h × 1000 kg/m³ = kg/h`
- 制冷功率：`Q = (kg/h × 4.186 kJ/(kg·°C) × ΔT°C) / 3600 s = flow_rate_m3h × 1.163 × ΔT [kW]`

**COP 计算：**

```
COP = Q_cooling / W_input
    = (flow_rate_m3h × 1.163 × |return_temp - supply_temp|) / (hvac_kwh / hours)
```

其中：
- `flow_rate_m3h`：冷冻水流量（m³/h）
- `return_temp`：回水温度（°C）
- `supply_temp`：供水温度（°C）
- `hvac_kwh`：HVAC 系统总用电量（kWh）
- `hours`：统计时间段长度（h），默认为 1

### 6.2 实现细节

代码位置：`backend/app/utils/cop.py`

边界条件处理：
- `hvac_kwh <= 0`：返回 `None`（无有效输入功率）
- `flow_rate_m3h <= 0`：返回 `None`（无有效流量）
- `supply_temp` 或 `return_temp` 缺失：返回 `None`
- `|ΔT| < 0.1°C`：返回 `None`（温差过小，数据无意义）

### 6.3 COP 评级

| COP 范围 | 评级 | 说明 |
|----------|------|------|
| > 4.0 | excellent | 系统运行效率优秀 |
| 3.0 ~ 4.0 | good | 系统运行正常 |
| 2.0 ~ 3.0 | fair | 效率偏低，建议关注 |
| < 2.0 | poor | 效率异常，需要检修 |

---

## 7. 部署方案

### 7.1 开发环境

**后端启动：**

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端启动：**

```bash
cd frontend
npm run dev
```

Vite 开发服务器默认运行在 `http://localhost:5173`，通过 CORS 中间件跨域访问后端 API。

### 7.2 生产部署

**后端：**

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

可选方案：使用 `gunicorn` 管理 `uvicorn` worker：

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**前端构建：**

```bash
cd frontend
npm run build    # 执行 vue-tsc -b && vite build
```

构建产物输出到 `frontend/dist/`，可通过 Nginx 静态托管或直接集成到 FastAPI 的静态文件服务。

### 7.3 环境依赖

| 服务 | 说明 |
|------|------|
| PostgreSQL | 主数据库，存储建筑、能耗、设备、异常事件 |
| SiliconFlow API | LLM 推理接口（Qwen2.5-7B-Instruct + bge-m3 Embedding） |
| Python >= 3.10 | 后端运行时 |
| Node.js | 前端构建工具链 |

### 7.4 配置管理

通过 `pydantic-settings` 管理配置，支持 `.env` 文件和环境变量覆盖：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `POSTGRES_HOST` | localhost | 数据库地址 |
| `POSTGRES_PORT` | 5432 | 数据库端口 |
| `LLM_API_BASE` | https://api.siliconflow.cn/v1 | LLM API 地址 |
| `LLM_MODEL_NAME` | Qwen/Qwen2.5-7B-Instruct | 推理模型 |
| `EMBEDDING_MODEL_NAME` | BAAI/bge-m3 | 嵌入模型 |
| `EMBEDDING_DIMENSIONS` | 1024 | 嵌入向量维度 |
| `APP_HOST` | 0.0.0.0 | 应用监听地址 |
| `APP_PORT` | 8000 | 应用监听端口 |
