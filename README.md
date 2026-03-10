# AERO - 建筑能源智能管理系统

建筑运维管理综合数字化平台，提供统一的能耗数据管理、查询统计、异常检测和智能问答能力。

## 功能特性

- **建筑与能耗管理** — 多建筑数据录入、导入与管理
- **多维度查询统计** — 按建筑/时间/能源类型聚合分析
- **异常智能检测** — 基于阈值的电力尖峰、COP 异常、温度偏差检测
- **HVAC COP 能效分析** — 制冷/制热系统能效比计算与趋势分析
- **智能问答** — 基于 LightRAG 知识图谱的建筑能耗问答
- **可视化与导出** — ECharts 交互图表、Excel 报表导出

## 技术栈

| 层 | 技术 |
|------|------|
| 后端 | FastAPI · SQLAlchemy (async) · PostgreSQL · Alembic |
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
│   │   ├── models/              # ORM 模型
│   │   ├── schemas/             # 数据验证 Schema
│   │   ├── services/            # 业务逻辑层
│   │   ├── routers/             # API 路由
│   │   ├── detection/           # 异常检测策略
│   │   ├── rag/                 # LightRAG 集成
│   │   ├── etl/                 # ETL 数据适配器
│   │   └── mcp/                 # MCP 协议支持
│   ├── alembic/                 # 数据库迁移
│   ├── scripts/                 # 工具脚本 (种子数据等)
│   └── .env.example             # 环境变量模板
├── frontend/
│   ├── src/
│   │   ├── api/                 # API 客户端
│   │   ├── components/          # Vue 组件 (图表/布局/问答)
│   │   ├── views/               # 页面视图
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── types/               # TypeScript 类型定义
│   │   └── router/              # 路由配置
│   └── vite.config.ts           # Vite 构建配置
└── docs/                        # 技术文档
```

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
POSTGRES_PASSWORD=your_password
LLM_API_KEY=sk-your-api-key

# 可选：启用 LightRAG 知识问答
ENABLE_LIGHTRAG_SERVER=true
```

完整配置选项见 `backend/.env.example`，支持 OpenAI 兼容 API、Ollama 本地模型等多种 LLM 配置。

### 3. 初始化数据库

```bash
cd backend
uv run alembic upgrade head
```

### 4. 启动服务

```bash
# 终端 1：后端
cd backend
uv run uvicorn app.main:app --reload --port 8000

# 终端 2：前端
cd frontend
npm run dev
```

访问 http://localhost:3000

## API 概览

| 模块 | 路径 | 说明 |
|------|------|------|
| 建筑管理 | `/api/v1/buildings` | 建筑 CRUD |
| 能耗查询 | `/api/v1/energy` | 能耗数据查询 |
| 统计分析 | `/api/v1/statistics` | 聚合统计、COP 计算 |
| 异常检测 | `/api/v1/anomaly` | 智能异常检测 |
| 设备管理 | `/api/v1/equipment` | 设备信息管理 |
| 数据导入 | `/api/v1/import` | 批量数据导入 |
| 数据导出 | `/api/v1/export` | Excel 报表导出 |
| 智能问答 | `/api/v1/qa` | 知识图谱问答 |

API 文档：启动后端后访问 http://localhost:8000/docs

## License

MIT
