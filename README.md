# AERO - 建筑能源智能管理系统

Building Energy Intelligent Management System with Full HVAC Chain

## 功能特性

- **建筑能耗管理** — 多建筑能耗数据录入、分项计量（电/暖通/照明/插座/燃气/水）
- **HVAC 全链路监测** — 冷水机组、AHU、锅炉、VAV、水泵、冷却塔运行数据采集与监测
- **设备台账管理** — 设备基本信息、额定参数、分系统管理
- **多维度统计分析** — COP 能效比、EUI 能耗指标、冷站综合效率计算
- **异常智能检测** — COP 异常、温差异常、AHU 同时加热制冷、VAV 区域过热/过冷等 8 类检测规则
- **智能问答** — 基于 LightRAG 知识图谱的建筑能耗问答
- **MCP 协议支持** — 标准 MCP 服务端，支持 AI 客户端接入
- **数据导入导出** — CSV/JSON 导入、CSV/Excel 导出

## 技术栈

| 层 | 技术 |
|------|------|
| 后端 | FastAPI · SQLAlchemy (async) · PostgreSQL |
| 前端 | Vue 3 · TypeScript · Vite · Naive UI · ECharts |
| AI | LightRAG · OpenAI 兼容 API / Ollama |
| 工具 | uv (Python) · npm (Node.js) |

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理 (Pydantic Settings)
│   │   ├── database.py          # 数据库连接
│   │   ├── models/              # ORM 模型 (11 张表)
│   │   ├── schemas/             # Pydantic 数据验证
│   │   ├── services/            # 业务逻辑层
│   │   ├── routers/             # API 路由
│   │   ├── detection/           # 异常检测策略
│   │   ├── rag/                 # LightRAG 集成
│   │   └── mcp/                 # MCP 协议支持
│   ├── sql/                     # 数据库建表 SQL
│   ├── scripts/                 # 工具脚本 (数据生成)
│   └── .env.example             # 环境变量模板
├── frontend/
│   ├── src/
│   │   ├── api/                 # API 客户端
│   │   ├── components/          # Vue 组件 (图表/布局)
│   │   ├── views/               # 页面视图
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── types/               # TypeScript 类型定义
│   │   └── router/              # 路由配置
│   └── vite.config.ts
└── docs/                        # 技术文档
```

## 数据模型

系统包含 11 张核心数据表：

| 表 | 说明 |
|------|------|
| `buildings` | 建筑基本信息（含气候区、设计负荷） |
| `weather_records` | 气象数据（干/湿球温度、风速、辐射） |
| `energy_meters` | 建筑能耗分项计量 |
| `equipment` | 设备台账（含型号、额定参数、COP） |
| `chiller_records` | 冷水机组运行数据（CHW/CW 回路、COP） |
| `ahu_records` | AHU 运行数据（SAT/RAT/MAT/OAT、阀位） |
| `boiler_records` | 锅炉运行数据（供回水温、效率） |
| `vav_records` | VAV 末端数据（区域温度、CO2、风量） |
| `pump_records` | 水泵运行数据（频率、流量、压差） |
| `cooling_tower_records` | 冷却塔运行数据（逼近度、冷幅） |
| `anomaly_events` | 异常事件（含故障代码、建议措施） |

## 快速开始

### 环境要求

- Python >= 3.11 + [uv](https://docs.astral.sh/uv/)
- Node.js >= 18 + npm
- PostgreSQL >= 14

### 1. 安装依赖

```bash
# 后端
cd backend
uv sync

# 前端
cd frontend
npm install
```

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
```

编辑 `backend/.env`，填写数据库连接和 LLM API 密钥：

```env
# 必填
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# 可选：配置 LLM（用于智能问答）
LLM_PROVIDER=api
LLM_API_KEY=sk-your-api-key
```

完整配置选项见 `backend/.env.example`。

### 3. 初始化数据库

在 PostgreSQL 中创建数据库，然后执行建表 SQL：

```bash
# 创建数据库
createdb aero

# 执行建表脚本
psql -d aero -f backend/sql/manual_tables.sql
```

### 4. 生成模拟数据（可选）

```bash
cd backend
# 生成数据并直接写入数据库（默认 7 天）
uv run python -m scripts.generate_data --days 30 --seed 42

# 如果数据库已有数据，使用 --reset 清空后重新生成
uv run python -m scripts.generate_data --days 30 --seed 42 --reset

# 仅导出 JSON 文件，不写入数据库
uv run python -m scripts.generate_data --days 30 --seed 42 --json-only

# 生成“按设备上传”的演示文件（不同设备不同字段/格式，含随机异常）
uv run python -m scripts.generate_data --days 7 --seed 42 --anomaly-rate 0.08 --json-only --upload-files

# 生成“按设备类型上传”的演示文件（推荐：先在系统里手动创建区域/建筑/设备）
uv run python -m scripts.generate_data --days 7 --seed 42 --anomaly-rate 0.08 --json-only --upload-files-by-type --upload-output-dir type_upload_files
```

生成内容包括：5 栋建筑、完整设备台账、气象数据、能耗数据、HVAC 运行数据、异常事件。
数据直接写入 PostgreSQL，无需额外导入步骤。

若启用 `--upload-files`，会额外在 `backend/data/upload_files/` 下生成每台设备对应文件，
可在页面的“设备上传数据”按钮中按设备 ID 手动上传；同时生成 `upload_manifest.json` 便于对照文件和设备。

若启用 `--upload-files-by-type`，会在指定目录（如 `backend/data/type_upload_files/`）生成每种设备类型一个样例文件
（`sample_chiller.csv`、`sample_ahu.json` 等），你可以在设备上传页选择任意同类型设备上传该文件。

### 5. 启动服务

```bash
# 终端 1：后端
cd backend
uv run uvicorn app.main:app --reload --port 8000

# 终端 2：前端
cd frontend
npm run dev
```

访问 http://localhost:3000

## 页面说明

| 路径 | 页面 | 功能 |
|------|------|------|
| `/dashboard` | 运行总览 | KPI 指标、能耗趋势、告警列表 |
| `/buildings` | 建筑管理 | 建筑信息 CRUD |
| `/energy` | 能耗监测 | 分项能耗查询、趋势图、饼图、CRUD |
| `/hvac` | 暖通监测 | 冷站/AHU/末端/热源 四 Tab 监测 |
| `/equipment` | 设备台账 | 设备信息管理（按系统分类） |
| `/statistics` | 统计分析 | COP、EUI、冷站效率 |
| `/anomaly` | 异常检测 | 多类型异常检测与告警 |
| `/import` | 数据管理 | CSV/JSON 文件上传导入 |
| `/qa` | 智能问答 | LightRAG 知识图谱问答 |
| `/mcp` | MCP 服务 | MCP 配置与状态管理 |

## API 概览

| 模块 | 路径 | 说明 |
|------|------|------|
| 建筑管理 | `/api/v1/buildings` | 建筑 CRUD |
| 气象数据 | `/api/v1/weather` | 气象记录查询与导入 |
| 能耗计量 | `/api/v1/energy-meters` | 分项能耗数据 CRUD |
| 设备台账 | `/api/v1/equipment` | 设备信息管理 |
| HVAC 数据 | `/api/v1/hvac` | 6 类设备运行数据 CRUD + 总览 |
| 统计分析 | `/api/v1/statistics` | COP/EUI/冷站效率/聚合 |
| 异常检测 | `/api/v1/anomaly` | 异常检测与告警管理 |
| 数据导入 | `/api/v1/import` | 批量数据导入 |
| 数据导出 | `/api/v1/export` | CSV/Excel 导出 |
| 智能问答 | `/api/v1/knowledge` | 知识图谱问答 |
| MCP 管理 | `/api/v1/mcp` | MCP 服务状态与配置 |

API 文档：启动后端后访问 http://localhost:8000/docs

### 导入格式

- 接口：`POST /api/v1/import/upload`
- 支持文件：`.csv`、`.json`
- CSV 表头示例（至少需要 `building_id` 和 `timestamp`）：

```csv
building_id,timestamp,total_electricity_kwh,hvac_electricity_kwh,lighting_kwh,plug_load_kwh,peak_demand_kw,gas_m3,water_m3,cooling_kwh,heating_kwh
```

- JSON 格式：`{"records": [...]}` 或直接数组

### 导出格式

- CSV：`POST /api/v1/export/csv`
- Excel：`POST /api/v1/export/excel`（含统计摘要和建筑汇总 Sheet）

## MCP 服务接入

AERO 提供标准 `streamable-http` MCP 服务端，默认端点：`http://localhost:8000/mcp/`

管理接口：

- `GET /api/v1/mcp/status` — 服务状态、工具列表
- `GET /api/v1/mcp/config` — Claude Desktop / Cherry Studio 可导入的 JSON

Cherry Studio 配置示例：

```json
{
  "mcpServers": {
    "aero-energy": {
      "type": "streamableHttp",
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

## License

MIT
