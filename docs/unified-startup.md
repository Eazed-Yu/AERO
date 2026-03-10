# AERO 统一启动方案

## 架构

```
AERO 后端 (uvicorn)
  ├─ FastAPI 主服务 (5000)
  └─ LightRAG 子进程 (8030)
       └─ Web UI + API

AERO 前端 (5173)
  └─ QAView (iframe → localhost:8030)
```

## 单一入口启动

### 1. 安装依赖

```bash
cd backend
uv sync
```

这会自动安装 `lightrag-hku[api]`，包含 Web UI。

### 2. 配置环境变量

编辑 `backend/.env`：

```env
LLM_API_KEY=sk-your-api-key
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus
EMBEDDING_MODEL_NAME=text-embedding-v3
EMBEDDING_DIMENSIONS=1024
```

### 3. 启动（单一命令）

```bash
# 启动后端（自动启动 LightRAG）
cd backend
uv run uvicorn app.main:app --reload --port 5000

# 启动前端
cd frontend
npm run dev
```

访问 http://localhost:5173

## 工作原理

1. AERO 后端启动时，`lifespan` 自动启动 LightRAG 子进程
2. LightRAG 监听 8030 端口，提供 Web UI
3. 前端通过 iframe 嵌入 LightRAG UI
4. 后端关闭时自动停止 LightRAG

## 依赖管理

- 所有依赖统一在 `backend/pyproject.toml`
- LightRAG 版本：`lightrag-hku[api]>=1.4.9`
- 配置统一在 `backend/app/config.py`

## 优势

