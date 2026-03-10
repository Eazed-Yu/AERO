# AERO 建筑能源智能管理系统 - 需求规格说明书

|  项目  |  内容  |
|--------|--------|
| 项目名称 | AERO - 建筑能源智能管理系统 |
| 版本 | v0.1.0 |
| 编写日期 | 2026-03-09 |
| 文档状态 | 初稿 |

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统范围](#2-系统范围)
3. [用户角色](#3-用户角色)
4. [功能需求](#4-功能需求)
5. [非功能需求](#5-非功能需求)
6. [约束条件](#6-约束条件)
7. [接口需求](#7-接口需求)
8. [数据需求](#8-数据需求)

---

## 1. 项目概述

### 1.1 背景

随着国家"碳达峰、碳中和"战略目标的推进，建筑领域作为能源消耗的主要部分，亟需通过智能化手段实现精细化能源管理。建筑能耗约占全社会总能耗的 30% 以上，涵盖电力、燃气、用水以及暖通空调（HVAC）等多种能源类型。传统的人工巡检与静态报表模式已无法满足现代建筑节能降碳的需求，迫切需要一套集数据采集、查询统计、异常检测和智能问答于一体的综合管理系统。

### 1.2 项目目标

AERO（Architecture Energy Resource Optimizer）建筑能源智能管理系统旨在为建筑运维团队和管理决策者提供一个统一的数字化平台，实现以下核心目标：

- **数据集中管理**：对多栋建筑、多类型能耗数据进行标准化采集、存储与管理。
- **多维查询统计**：支持按建筑、时间、指标等多条件灵活查询，并提供多粒度时段汇总。
- **异常智能检测**：基于阈值规则自动识别能耗异常，预留机器学习检测接口以支持后续扩展。
- **COP 分析**：计算并追踪暖通空调系统的能效系数（Coefficient of Performance），辅助节能优化。
- **可视化与报表**：通过趋势图表和导出报表，直观呈现能耗态势，辅助管理决策。
- **智能问答**：基于 LightRAG 知识图谱，提供建筑能源领域的自然语言问答能力。

### 1.3 项目范围

本系统面向山东省内典型建筑场景（办公楼、商业综合体、住宅小区、医院、学校），以演示验证为首要目标，数据来源为模拟生成的标准格式数据。系统采用前后端分离架构，后端提供 REST API，前端提供 Web 管理界面。

---

## 2. 系统范围

### 2.1 模块划分

系统由以下四大核心模块组成：

| 模块编号 | 模块名称 | 功能概述 |
|----------|----------|----------|
| M1 | 数据管理模块 | 建筑信息管理、能耗数据导入（JSON/CSV）、设备台账管理、数据校验 |
| M2 | 查询统计模块 | 多条件能耗查询、分页浏览、多粒度时段聚合统计、COP 计算与分析 |
| M3 | 异常检测模块 | 基于阈值的异常自动检测、异常事件管理、异常统计汇总、ML 扩展接口 |
| M4 | 智能问答模块 | 基于 LightRAG 的知识图谱构建、多模式检索问答、文档导入与管理 |

### 2.2 辅助功能

| 功能 | 说明 |
|------|------|
| 可视化图表 | 能耗趋势折线图、能耗构成饼图、COP 趋势图、异常散点图 |
| 报表导出 | 支持 CSV 和 Excel 格式导出 |
| 设备监控 | 设备运行状态查询、状态历史追踪 |
| 健康检查 | 系统运行状态及 LightRAG 可用性检测 |

### 2.3 系统边界

- **系统内**：数据导入、存储、查询、统计、异常检测、可视化展示、智能问答。
- **系统外**：物理传感器数据采集（本系统使用模拟数据）、第三方告警推送、用户权限认证（当前版本不实现）。

---

## 3. 用户角色

| 角色 | 角色标识 | 职责描述 | 使用场景 |
|------|----------|----------|----------|
| 运维人员 | Operator | 负责日常能耗数据监控、异常事件处理、设备状态巡查 | 查询能耗数据、查看异常告警、确认或解决异常事件、查看设备运行状态 |
| 管理人员 | Manager | 负责能耗趋势分析、节能决策支持、报表审阅 | 查看统计汇总与图表、导出报表、使用智能问答获取分析建议 |
| 系统管理员 | Admin | 负责系统配置、数据导入、知识库维护 | 导入能耗数据、管理建筑与设备信息、维护知识库文档 |

> 注：当前版本为演示系统，暂不实现用户认证与权限控制。上述角色划分用于明确功能面向的使用场景。

---

## 4. 功能需求

### FR-001 数据导入

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-001 |
| 需求名称 | 能耗数据导入 |
| 优先级 | 高 |
| 所属模块 | M1 - 数据管理 |

#### 描述

系统应支持将标准格式的建筑能耗数据批量导入到数据库中，提供两种导入方式：结构化 JSON Body 导入和文件上传导入。

#### 功能点

1. **JSON Body 批量导入**
   - 接收符合 `EnergyRecordCreate` schema 的记录数组。
   - 支持冲突处理策略（`on_conflict`）：`skip`（跳过重复）、`update`（覆盖更新）、`error`（报错终止）。
   - 可选开启数据校验（`validate` 参数）。

2. **文件上传导入**
   - 支持 CSV 文件上传（自动解析表头映射字段）。
   - 支持 JSON 文件上传（数组格式）。
   - 逐行校验，记录校验失败的行号及原因。

3. **导入结果反馈**
   - 返回 `ImportResult`，包含以下字段：
     - `total`：提交总数。
     - `inserted`：成功插入数。
     - `skipped`：跳过数。
     - `errors`：错误数。
     - `error_details`：前 20 条错误详情。

#### 输入

- JSON Body：`EnergyImportRequest`（`records` 数组 + `on_conflict` 策略 + `validate` 开关）。
- 文件：CSV 或 JSON 文件（`multipart/form-data`）。

#### 输出

- `ImportResult` 对象。

---

### FR-002 多条件能耗查询

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-002 |
| 需求名称 | 多条件能耗查询 |
| 优先级 | 高 |
| 所属模块 | M2 - 查询统计 |

#### 描述

系统应支持对能耗记录按多维度条件进行筛选查询，返回分页结果。

#### 功能点

1. **筛选条件**
   - `building_id`：按建筑 ID 筛选（可选）。
   - `start_time` / `end_time`：按时间范围筛选（可选）。
   - `metrics`：指定返回的能耗指标字段，逗号分隔（可选，例如 `electricity_kwh,water_m3`）。

2. **分页与排序**
   - `page`：页码，从 1 开始，默认 1。
   - `page_size`：每页记录数，范围 1-1000，默认 50。
   - `sort_by`：排序字段，默认 `timestamp`。
   - `sort_order`：排序方向，`asc` 或 `desc`，默认 `desc`。

3. **返回结果**
   - 分页响应（`PaginatedResponse`），包含：
     - `items`：当前页的 `EnergyRecordResponse` 数组。
     - `total`：总记录数。
     - `page` / `page_size` / `pages`：分页信息。

#### 输入

- Query Parameters：`building_id`, `start_time`, `end_time`, `metrics`, `page`, `page_size`, `sort_by`, `sort_order`。

#### 输出

- `PaginatedResponse` 对象。

---

### FR-003 时段汇总统计

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-003 |
| 需求名称 | 时段汇总统计 |
| 优先级 | 高 |
| 所属模块 | M2 - 查询统计 |

#### 描述

系统应支持按不同时间粒度对能耗指标进行聚合统计，用于趋势分析和对比。

#### 功能点

1. **聚合粒度**
   - 支持四种聚合周期：`hour`（小时）、`day`（日）、`week`（周）、`month`（月）。

2. **聚合指标**
   - 支持对多个能耗字段进行聚合，通过 `metrics` 参数指定（逗号分隔）。
   - 默认聚合 `electricity_kwh`。

3. **聚合结果**
   - 每个时段返回一个 `AggregationResult`，包含：
     - `period_start` / `period_end`：时段起止时间。
     - `metric_name`：指标名称。
     - `avg`：平均值。
     - `min`：最小值。
     - `max`：最大值。
     - `sum`：累计值。
     - `count`：数据点数。

#### 输入

- Query Parameters：`building_id`（必填）、`start_time`（必填）、`end_time`（必填）、`period`、`metrics`。

#### 输出

- `AggregationResult` 数组。

---

### FR-004 COP 计算与分析

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-004 |
| 需求名称 | COP 计算与分析 |
| 优先级 | 中 |
| 所属模块 | M2 - 查询统计 |

#### 描述

系统应支持计算暖通空调系统的能效系数（COP），辅助评估 HVAC 系统运行效率。

#### 功能点

1. **COP 计算公式**
   ```
   COP = Q_cooling / W_input
   Q_cooling = flow_rate_m3h × 1.163 × |return_temp - supply_temp|  [kW]
   W_input = hvac_kwh / hours  [kW]
   ```
   其中 1.163 = 1000 kg/m³ × 4.186 kJ/(kg·K) / 3600 s。

2. **按时段聚合 COP**
   - 支持按 `hour` / `day` / `week` / `month` 粒度计算。

3. **COP 评级**
   - `excellent`（优秀）：COP > 4.0
   - `good`（良好）：COP > 3.0
   - `fair`（一般）：COP > 2.0
   - `poor`（较差）：COP <= 2.0

4. **返回结果**
   - 每个时段返回一个 `COPResult`，包含：
     - `period_start`：时段起始时间。
     - `cop`：COP 值。
     - `cooling_output_kwh`：制冷/制热输出量。
     - `energy_input_kwh`：能源输入量。
     - `avg_supply_temp` / `avg_return_temp`：平均供回水温度。
     - `rating`：效率评级。

#### 输入

- Query Parameters：`building_id`（必填）、`start_time`（必填）、`end_time`（必填）、`period`。

#### 输出

- `COPResult` 数组。

---

### FR-005 数据异常分析

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-005 |
| 需求名称 | 数据异常分析 |
| 优先级 | 高 |
| 所属模块 | M3 - 异常检测 |

#### 描述

系统应支持对能耗数据进行自动异常检测，当前实现基于阈值规则的检测策略，并预留机器学习检测接口。

#### 功能点

1. **阈值检测（ThresholdDetector）**
   - **电力尖峰检测**：当电力消耗超过区间均值的指定倍数时触发（默认 2.0 倍）。
   - **COP 异常检测**：当 COP 低于最低阈值时触发（默认 2.0）。
   - **温度偏差检测**：当供水温度偏离期望值超过阈值时触发（默认 5.0°C）。
     - 制冷模式期望供水温度：7.0°C（室外温度 > 22°C 时）。
     - 制热模式期望供水温度：45.0°C（室外温度 <= 22°C 时）。

2. **异常严重度分级**
   - `low`（低）、`medium`（中）、`high`（高）、`critical`（严重）。
   - 电力尖峰严重度根据超标比率自动判定（1.5x: low, 2.0x: medium, 3.0x: critical）。
   - COP 异常：COP < 1.0 为 `high`，其余为 `medium`。

3. **异常事件管理**
   - 查询异常列表：支持按 `building_id`、`severity`、`resolved`、时间范围筛选。
   - 标记已解决：将异常事件标记为已处理（`PATCH /{anomaly_id}/resolve`）。

4. **异常统计汇总**
   - 按异常类型统计数量（`by_type`）。
   - 按严重度统计数量（`by_severity`）。
   - 统计未解决异常数量（`unresolved_count`）。

5. **ML 检测接口预留**
   - 系统定义了 `AbstractDetector` 抽象基类，包含 `detect(records, context)` 接口。
   - 已创建 `MLDetector` 占位实现，后续可接入机器学习模型。

#### 输入

- 触发检测：`AnomalyDetectRequest`（`building_id`、`start_time`、`end_time`）。
- 查询列表：Query Parameters（`building_id`、`severity`、`resolved`、`start_time`、`end_time`、`limit`）。

#### 输出

- `AnomalyEventResponse` 数组 / 异常统计汇总。

---

### FR-006 可视化图表展示

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-006 |
| 需求名称 | 可视化图表展示 |
| 优先级 | 中 |
| 所属模块 | 前端展示 |

#### 描述

系统前端应提供多种 ECharts 图表组件，直观展示能耗数据及分析结果。

#### 功能点

1. **能耗趋势折线图（EnergyTrendChart）**
   - 展示选定建筑在指定时段内的能耗指标随时间的变化趋势。
   - 支持多指标叠加显示。

2. **能耗构成饼图（EnergyDistributionChart）**
   - 展示选定建筑各类能耗（电力、水、燃气、HVAC）的占比构成。

3. **COP 趋势图（COPTrendChart）**
   - 展示 COP 值随时间的变化趋势。
   - 标注 COP 评级参考线。

4. **异常散点图（AnomalyScatterChart）**
   - 在时间轴上展示异常事件的分布情况。
   - 以颜色/大小区分异常严重度。

#### 技术实现

- 基于 ECharts 5.5 + vue-echarts 7.0 组件库。

---

### FR-007 报表导出

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-007 |
| 需求名称 | 报表导出 |
| 优先级 | 中 |
| 所属模块 | M2 - 查询统计 |

#### 描述

系统应支持将能耗数据导出为通用文件格式，便于离线分析和报告编制。

#### 功能点

1. **CSV 导出**
   - 导出指定建筑、指定时间范围内的能耗数据为 CSV 文件。
   - 导出字段：`building_id`, `timestamp`, `electricity_kwh`, `water_m3`, `gas_m3`, `hvac_kwh`, `hvac_supply_temp`, `hvac_return_temp`, `outdoor_temp`, `outdoor_humidity`。
   - 文件命名格式：`energy_{building_id}_{start_date}_{end_date}.csv`。

2. **Excel 导出**
   - 导出相同数据为 Excel（.xlsx）文件。
   - Sheet 名称：`能耗数据`。
   - 文件命名格式：`energy_{building_id}_{start_date}_{end_date}.xlsx`。

#### 输入

- `building_id`（必填）、`start_time`（必填）、`end_time`（必填）。

#### 输出

- 文件流（`StreamingResponse` 或二进制响应）。

---

### FR-008 设备运行状态监控

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-008 |
| 需求名称 | 设备运行状态监控 |
| 优先级 | 中 |
| 所属模块 | M1 - 数据管理 |

#### 描述

系统应支持查看建筑内各设备的基本信息和运行状态历史。

#### 功能点

1. **设备列表查询**
   - 查询所有设备，支持按 `building_id` 和 `device_type` 筛选。
   - 设备类型包括：`chiller`（冷水机）、`ahu`（空气处理机组）、`pump`（水泵）、`lighting`（照明系统）、`elevator`（电梯）、`boiler`（锅炉）等。

2. **设备详情**
   - 查看指定设备的基本信息及最新运行状态。
   - 设备信息包含：`device_id`、`device_name`、`device_type`、`rated_power_kw`、`install_date`。

3. **状态历史查询**
   - 查询指定设备在指定时间范围内的运行状态记录。
   - 状态字段：`status`（`normal` / `abnormal` / `offline` / `maintenance`）、`power_consumption_kw`、`runtime_hours`、`error_code`、`notes`。

#### 输入

- Query Parameters：`building_id`、`device_type`、`device_id`、`start_time`、`end_time`、`limit`。

#### 输出

- `EquipmentResponse` 数组 / 设备详情 + 最新状态 / `EquipmentStatusResponse` 数组。

---

### FR-009 智能问答

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-009 |
| 需求名称 | 智能问答 |
| 优先级 | 中 |
| 所属模块 | M4 - 智能问答 |

#### 描述

系统应提供基于 LightRAG 知识图谱的自然语言问答能力，用户可通过自然语言提问获取建筑能源相关知识。

#### 功能点

1. **问答查询**
   - 用户输入自然语言问题。
   - 系统基于 LightRAG 进行检索并生成回答。
   - 返回回答文本、检索模式和处理耗时。

2. **检索模式**
   - `local`（局部检索）：检索与问题直接相关的实体和关系。
   - `global`（全局检索）：跨文档集合的广泛知识图谱检索。
   - `hybrid`（混合检索）：结合局部和全局检索（推荐默认模式）。
   - `naive`（朴素检索）：简单的向量相似度检索。

3. **可用性检查**
   - 系统启动时自动初始化 LightRAG 服务。
   - 若 LightRAG 不可用，Q&A 接口返回 503 状态码。
   - 健康检查接口返回 `rag_available` 字段标识可用性。

#### 输入

- `QAQueryRequest`：`question`（问题文本，必填）、`mode`（检索模式，默认 `hybrid`）。

#### 输出

- `QAQueryResponse`：`answer`（回答文本）、`mode_used`（使用的检索模式）、`processing_time_ms`（处理耗时，毫秒）。

---

### FR-010 知识库管理

| 属性 | 内容 |
|------|------|
| 需求编号 | FR-010 |
| 需求名称 | 知识库管理 |
| 优先级 | 低 |
| 所属模块 | M4 - 智能问答 |

#### 描述

系统应支持向 LightRAG 知识库导入文本文档，用于构建和扩充知识图谱。

#### 功能点

1. **文档导入**
   - 提交文本内容和来源标识，系统自动将其写入 LightRAG 索引。
   - 支持通过 `QAIngestRequest` 提交：`text`（文本内容，必填）、`source`（来源标识，可选）。

2. **知识图谱构建**
   - LightRAG 自动从导入文本中抽取实体和关系，构建知识图谱。
   - 使用 SiliconFlow 平台的 LLM（`Qwen/Qwen2.5-7B-Instruct`）进行实体抽取。
   - 使用 `BAAI/bge-m3` 模型进行文本 Embedding（维度 1024）。

3. **检索模式查询**
   - 提供接口列出所有可用的检索模式及其说明。

#### 输入

- `QAIngestRequest`：`text`（文本内容）、`source`（来源标识）。

#### 输出

- 导入结果状态。

---

## 5. 非功能需求

### 5.1 响应速度

| 编号 | 需求项 | 指标 | 级别 |
|------|--------|------|------|
| NFR-001 | API 响应时间 | 常规查询接口响应时间 < 3 秒（演示级） | 演示级 |
| NFR-002 | 聚合统计响应 | 时段汇总统计接口响应时间 < 5 秒（演示级） | 演示级 |
| NFR-003 | 异常检测响应 | 单次异常检测请求响应时间 < 10 秒（演示级） | 演示级 |
| NFR-004 | 智能问答响应 | LightRAG 问答响应时间 < 30 秒（依赖外部 LLM 服务） | 演示级 |
| NFR-005 | 页面加载 | 前端页面首屏加载时间 < 5 秒（本地网络） | 演示级 |

> 注：本系统定位为演示验证系统，响应速度指标以满足演示流畅性为标准，非生产级性能要求。

### 5.2 数据质量

| 编号 | 需求项 | 说明 |
|------|--------|------|
| NFR-006 | 格式规范 | 导入数据必须符合定义的标准格式（schema 校验），不符合格式的记录应被拒绝并返回错误详情 |
| NFR-007 | 数值约束 | 能耗数值（电力、水、燃气、HVAC）不允许为负值（数据库层 CHECK 约束） |
| NFR-008 | 无明显异常 | 模拟数据应符合实际物理规律，无明显不合理数值（如夏季制热、COP 异常高等） |
| NFR-009 | 时间完整性 | 能耗数据按小时粒度记录，时间序列应保持连续，无大段缺失 |

### 5.3 系统稳定性

| 编号 | 需求项 | 指标 |
|------|--------|------|
| NFR-010 | 连续运行 | 系统应能连续运行 30 分钟以上无崩溃或无响应 |
| NFR-011 | 错误处理 | 接口调用出错时应返回规范的 HTTP 错误码和错误信息，不应导致服务进程退出 |
| NFR-012 | 服务降级 | LightRAG 不可用时，系统其他功能（查询、统计、异常检测）应正常运行，仅问答功能不可用 |

---

## 6. 约束条件

### 6.1 技术栈要求

| 层次 | 技术选型 | 版本要求 |
|------|----------|----------|
| 后端框架 | FastAPI | >= 0.115.0 |
| 后端运行时 | Python | >= 3.10 |
| ASGI 服务器 | Uvicorn | >= 0.30.0 |
| 数据库 | PostgreSQL（asyncpg 驱动） | asyncpg >= 0.29.0 |
| ORM | SQLAlchemy（async 模式） | >= 2.0.0 |
| 数据库迁移 | Alembic | >= 1.13.0 |
| 知识图谱引擎 | LightRAG (HKU) | >= 1.4.9 |
| LLM 服务 | SiliconFlow（OpenAI 兼容 API） | Qwen/Qwen2.5-7B-Instruct |
| Embedding 模型 | BAAI/bge-m3 | 维度 1024 |
| Excel 处理 | openpyxl | >= 3.1.0 |
| 数据处理 | pandas / numpy | pandas >= 2.0, numpy >= 1.24 |
| 前端框架 | Vue 3 | >= 3.5.0 |
| 前端 UI 库 | Naive UI | >= 2.40.0 |
| 图表库 | ECharts + vue-echarts | ECharts >= 5.5, vue-echarts >= 7.0 |
| 状态管理 | Pinia | >= 2.2.0 |
| HTTP 客户端 | Axios | >= 1.7.0 |
| 前端路由 | Vue Router | >= 4.4.0 |
| 前端构建 | Vite | >= 6.0.0 |
| 类型检查 | TypeScript | ~5.6.0 |

### 6.2 数据来源

- 当前版本使用脚本生成的模拟数据（`scripts/generate_data.py`）。
- 模拟数据覆盖 5 栋典型建筑（办公楼、商业综合体、住宅小区、医院、学校）。
- 数据时间范围为 2025 年度。
- 能耗数据按小时粒度生成，包含季节性和日内波动规律。

### 6.3 部署约束

- 后端运行于 `0.0.0.0:8000`。
- 前端开发模式由 Vite 提供。
- 数据库为远程 PostgreSQL 实例。
- LightRAG 依赖 SiliconFlow 平台 API（需配置 `LLM_API_KEY`）。

---

## 7. 接口需求

### 7.1 REST API 列表

所有 API 以 `/api/v1` 为前缀。

#### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 系统健康检查，返回运行状态及 LightRAG 可用性 |

#### 建筑管理（/api/v1/buildings）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/buildings` | 查询建筑列表，支持 `building_type` 筛选 |
| GET | `/api/v1/buildings/{building_id}` | 获取指定建筑详情 |
| POST | `/api/v1/buildings` | 创建新建筑 |
| PUT | `/api/v1/buildings/{building_id}` | 更新建筑信息 |

#### 数据导入（/api/v1/import）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/import/energy` | JSON Body 批量导入能耗记录 |
| POST | `/api/v1/import/upload` | 文件上传导入（CSV/JSON） |

#### 能耗查询（/api/v1/energy）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/energy` | 多条件能耗查询，支持分页和排序 |

#### 统计分析（/api/v1/statistics）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/statistics/aggregate` | 时段汇总聚合统计 |
| GET | `/api/v1/statistics/cop` | COP 计算与分析 |
| GET | `/api/v1/statistics/anomaly-summary` | 异常事件统计汇总 |

#### 异常检测（/api/v1/anomaly）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/anomaly` | 查询异常事件列表 |
| POST | `/api/v1/anomaly/detect` | 触发异常检测 |
| PATCH | `/api/v1/anomaly/{anomaly_id}/resolve` | 标记异常已解决 |

#### 设备管理（/api/v1/equipment）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/equipment` | 查询设备列表 |
| GET | `/api/v1/equipment/{device_id}` | 获取设备详情及最新状态 |
| GET | `/api/v1/equipment/{device_id}/status-history` | 查询设备状态历史 |

#### 报表导出（/api/v1/export）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/export/csv` | 导出能耗数据为 CSV |
| POST | `/api/v1/export/excel` | 导出能耗数据为 Excel |

#### 智能问答（/api/v1/qa）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/qa/query` | 提交问题进行知识图谱问答 |
| POST | `/api/v1/qa/ingest` | 向知识库导入文本 |
| GET | `/api/v1/qa/modes` | 获取可用的检索模式列表 |

---

## 8. 数据需求

### 8.1 建筑信息（Building）

| 字段名 | 类型 | 必填 | 约束 | 说明 |
|--------|------|------|------|------|
| `building_id` | string | 是 | 最大 64 字符，唯一 | 建筑编号（如 `BLD-001`） |
| `name` | string | 是 | 最大 255 字符 | 建筑名称 |
| `building_type` | string | 是 | 最大 64 字符 | 建筑类型（`office` / `commercial` / `residential` / `hospital` / `school`） |
| `area` | float | 是 | > 0 | 建筑面积（m²） |
| `address` | string | 否 | - | 地址 |
| `floors` | int | 否 | - | 楼层数 |
| `year_built` | int | 否 | - | 建成年份 |

### 8.2 能耗记录（EnergyRecord）

| 字段名 | 类型 | 必填 | 约束 | 说明 |
|--------|------|------|------|------|
| `building_id` | string | 是 | 最大 64 字符，外键关联建筑 | 所属建筑编号 |
| `timestamp` | datetime | 是 | ISO 8601 格式 | 记录时间戳（小时粒度） |
| `electricity_kwh` | float | 否 | >= 0 | 电力消耗（kWh） |
| `water_m3` | float | 否 | >= 0 | 用水量（m³） |
| `gas_m3` | float | 否 | >= 0 | 燃气消耗（m³） |
| `hvac_kwh` | float | 否 | >= 0 | HVAC 能耗（kWh） |
| `hvac_supply_temp` | float | 否 | - | HVAC 供水温度（°C） |
| `hvac_return_temp` | float | 否 | - | HVAC 回水温度（°C） |
| `hvac_flow_rate` | float | 否 | >= 0 | HVAC 水流量（m³/h） |
| `outdoor_temp` | float | 否 | - | 室外温度（°C） |
| `outdoor_humidity` | float | 否 | - | 室外湿度（%） |
| `occupancy_density` | float | 否 | >= 0 | 人员密度（人/100m²） |

### 8.3 设备信息（Equipment）

| 字段名 | 类型 | 必填 | 约束 | 说明 |
|--------|------|------|------|------|
| `building_id` | string | 是 | 最大 64 字符 | 所属建筑编号 |
| `device_id` | string | 是 | 最大 128 字符，唯一 | 设备编号（如 `DEV-0001`） |
| `device_name` | string | 是 | 最大 255 字符 | 设备名称 |
| `device_type` | string | 是 | 最大 64 字符 | 设备类型（`chiller` / `ahu` / `pump` / `lighting` / `elevator` / `boiler`） |
| `rated_power_kw` | float | 否 | - | 额定功率（kW） |
| `install_date` | datetime | 否 | - | 安装日期 |

### 8.4 设备状态记录（EquipmentStatus）

| 字段名 | 类型 | 必填 | 约束 | 说明 |
|--------|------|------|------|------|
| `device_id` | string | 是 | 最大 128 字符 | 设备编号 |
| `timestamp` | datetime | 是 | ISO 8601 格式 | 状态记录时间 |
| `status` | string | 是 | 枚举：`normal` / `abnormal` / `offline` / `maintenance` | 运行状态 |
| `power_consumption_kw` | float | 否 | - | 实际功耗（kW） |
| `runtime_hours` | float | 否 | - | 运行时长（小时） |
| `error_code` | string | 否 | - | 故障代码 |
| `notes` | string | 否 | - | 备注 |

### 8.5 异常事件（AnomalyEvent）

| 字段名 | 类型 | 必填 | 约束 | 说明 |
|--------|------|------|------|------|
| `building_id` | string | 是 | 最大 64 字符 | 所属建筑编号 |
| `device_id` | string | 否 | - | 关联设备编号 |
| `timestamp` | datetime | 是 | - | 异常发生时间 |
| `anomaly_type` | string | 是 | 最大 64 字符 | 异常类型（`energy_spike` / `low_cop` / `temp_deviation`） |
| `severity` | string | 是 | 枚举：`low` / `medium` / `high` / `critical` | 严重程度 |
| `metric_name` | string | 是 | 最大 64 字符 | 异常指标名称 |
| `metric_value` | float | 是 | - | 异常指标值 |
| `threshold_value` | float | 否 | - | 阈值基准值 |
| `description` | string | 是 | - | 异常描述 |
| `detection_method` | string | 是 | 默认 `threshold` | 检测方法 |
| `resolved` | bool | 是 | 默认 `false` | 是否已解决 |

### 8.6 数据导入示例

#### JSON 格式

```json
{
  "building_id": "BLD-001",
  "timestamp": "2025-01-01T00:00:00",
  "electricity_kwh": 37.87,
  "water_m3": 1.454,
  "gas_m3": 2.164,
  "hvac_kwh": 25.76,
  "hvac_supply_temp": 44.8,
  "hvac_return_temp": 37.8,
  "hvac_flow_rate": 62.8,
  "outdoor_temp": -6.1,
  "outdoor_humidity": 48.3,
  "occupancy_density": 1.3
}
```

#### CSV 格式

```csv
building_id,timestamp,electricity_kwh,water_m3,gas_m3,hvac_kwh,hvac_supply_temp,hvac_return_temp,hvac_flow_rate,outdoor_temp,outdoor_humidity,occupancy_density
BLD-001,2025-01-01T00:00:00,37.87,1.454,2.164,25.76,44.8,37.8,62.8,-6.1,48.3,1.3
```

### 8.7 示例建筑数据

| 建筑编号 | 名称 | 类型 | 面积 (m²) | 地址 | 楼层 | 建成年份 |
|----------|------|------|-----------|------|------|----------|
| BLD-001 | 绿地办公大厦 | office | 15,000 | 济南市历下区经十路88号 | 20 | 2018 |
| BLD-002 | 中央商业广场 | commercial | 25,000 | 济南市市中区泉城路168号 | 6 | 2015 |
| BLD-003 | 滨河花园小区 | residential | 8,000 | 临沂市兰山区滨河大道56号 | 18 | 2020 |
| BLD-004 | 临朐县人民医院 | hospital | 20,000 | 潍坊市临朐县民主路100号 | 12 | 2012 |
| BLD-005 | 临沂大学教学楼A | school | 5,000 | 临沂市兰山区双岭路中段 | 5 | 2010 |
