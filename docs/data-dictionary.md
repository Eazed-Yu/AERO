# AERO 数据字典

> 本文档定义了 AERO 系统所有核心数据库表的结构、字段约束及说明。

---

## 目录

1. [buildings - 建筑信息表](#1-buildings---建筑信息表)
2. [energy_records - 能耗记录表](#2-energy_records---能耗记录表核心时序数据)
3. [equipment - 设备信息表](#3-equipment---设备信息表)
4. [equipment_status - 设备状态表](#4-equipment_status---设备状态表)
5. [anomaly_events - 异常事件表](#5-anomaly_events---异常事件表)
6. [标准数据导入格式](#6-标准数据导入格式)

---

## 1. buildings - 建筑信息表

存储所有纳管建筑的基本信息，是系统中其他表的核心关联实体。

| 字段名 | 数据类型 | 是否必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | PRIMARY KEY | 主键，由系统自动生成 |
| building_id | VARCHAR(64) | 是 | UNIQUE, NOT NULL | 建筑唯一业务编号，用于跨系统对接 |
| name | VARCHAR(255) | 是 | NOT NULL | 建筑名称 |
| building_type | VARCHAR(64) | 是 | NOT NULL | 建筑类型，枚举值见下方 |
| area | FLOAT | 是 | NOT NULL, CHECK (area > 0) | 建筑面积，单位：平方米 (m²) |
| address | VARCHAR(512) | 否 | - | 建筑地址 |
| floors | INTEGER | 否 | - | 建筑层数 |
| year_built | INTEGER | 否 | - | 建成年份 |
| created_at | TIMESTAMPTZ | 否 | DEFAULT NOW() | 记录创建时间（含时区） |
| updated_at | TIMESTAMPTZ | 否 | DEFAULT NOW() | 记录最后更新时间（含时区） |

**building_type 枚举值：**

| 值 | 说明 |
|---|---|
| office | 办公建筑 |
| commercial | 商业建筑 |
| residential | 住宅建筑 |
| hospital | 医院建筑 |
| school | 学校建筑 |

---

## 2. energy_records - 能耗记录表（核心时序数据）

存储各建筑的能耗与环境时序数据，是系统分析和异常检测的基础数据源。

| 字段名 | 数据类型 | 是否必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | BIGSERIAL | 是 | PRIMARY KEY | 自增主键 |
| building_id | VARCHAR(64) | 是 | FOREIGN KEY → buildings(building_id), NOT NULL | 关联建筑编号 |
| timestamp | TIMESTAMPTZ | 是 | NOT NULL | 数据采集时间戳（含时区） |
| electricity_kwh | FLOAT | 否 | CHECK (electricity_kwh >= 0) | 电力消耗，单位：千瓦时 (kWh) |
| water_m3 | FLOAT | 否 | CHECK (water_m3 >= 0) | 用水量，单位：立方米 (m³) |
| gas_m3 | FLOAT | 否 | CHECK (gas_m3 >= 0) | 燃气消耗，单位：立方米 (m³) |
| hvac_kwh | FLOAT | 否 | CHECK (hvac_kwh >= 0) | 暖通空调能耗，单位：千瓦时 (kWh) |
| hvac_supply_temp | FLOAT | 否 | - | 暖通空调供水温度，单位：摄氏度 (°C) |
| hvac_return_temp | FLOAT | 否 | - | 暖通空调回水温度，单位：摄氏度 (°C) |
| hvac_flow_rate | FLOAT | 否 | CHECK (hvac_flow_rate >= 0) | 暖通空调水流量，单位：m³/h |
| outdoor_temp | FLOAT | 否 | - | 室外温度，单位：摄氏度 (°C) |
| outdoor_humidity | FLOAT | 否 | - | 室外相对湿度，单位：百分比 (%) |
| occupancy_density | FLOAT | 否 | CHECK (occupancy_density >= 0) | 人员密度，单位：人/m² |
| created_at | TIMESTAMPTZ | 否 | DEFAULT NOW() | 记录创建时间（含时区） |

**索引：**

| 索引名 | 字段 | 说明 |
|---|---|---|
| idx_energy_records_building_ts | (building_id, timestamp DESC) | 按建筑和时间倒序的复合索引，用于加速时序查询 |

---

## 3. equipment - 设备信息表

存储建筑内各类机电设备的基本信息及额定参数。

| 字段名 | 数据类型 | 是否必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | PRIMARY KEY | 主键，由系统自动生成 |
| building_id | VARCHAR(64) | 否 | FOREIGN KEY → buildings(building_id) | 关联建筑编号 |
| device_id | VARCHAR(128) | 否 | UNIQUE | 设备唯一业务编号 |
| device_name | VARCHAR(255) | 否 | - | 设备名称 |
| device_type | VARCHAR(64) | 否 | - | 设备类型，枚举值见下方 |
| rated_power_kw | FLOAT | 否 | - | 额定功率，单位：千瓦 (kW) |

**device_type 枚举值：**

| 值 | 说明 |
|---|---|
| chiller | 冷水机组 |
| boiler | 锅炉 |
| ahu | 空气处理机组 (Air Handling Unit) |
| pump | 水泵 |
| lighting | 照明设备 |

---

## 4. equipment_status - 设备状态表

记录设备运行状态的时序数据，用于设备监控和故障分析。

| 字段名 | 数据类型 | 是否必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | BIGSERIAL | 是 | PRIMARY KEY | 自增主键 |
| device_id | VARCHAR(128) | 否 | FOREIGN KEY → equipment(device_id) | 关联设备编号 |
| timestamp | TIMESTAMPTZ | 否 | - | 状态采集时间戳（含时区） |
| status | VARCHAR(32) | 否 | - | 设备运行状态，枚举值见下方 |
| power_consumption_kw | FLOAT | 否 | - | 实时功率消耗，单位：千瓦 (kW) |
| runtime_hours | FLOAT | 否 | - | 累计运行时长，单位：小时 (h) |
| error_code | VARCHAR(64) | 否 | - | 故障代码，无故障时为空 |

**status 枚举值：**

| 值 | 说明 |
|---|---|
| normal | 正常运行 |
| abnormal | 运行异常 |
| offline | 离线 |
| maintenance | 维护中 |

---

## 5. anomaly_events - 异常事件表

记录系统检测到的各类异常事件，支持阈值规则和机器学习两种检测方式。

| 字段名 | 数据类型 | 是否必填 | 约束 | 说明 |
|---|---|---|---|---|
| id | UUID | 是 | PRIMARY KEY | 主键，由系统自动生成 |
| building_id | VARCHAR(64) | 否 | FOREIGN KEY → buildings(building_id) | 关联建筑编号 |
| device_id | VARCHAR(128) | 否 | FOREIGN KEY → equipment(device_id), NULLABLE | 关联设备编号，建筑级异常时为空 |
| timestamp | TIMESTAMPTZ | 否 | - | 异常发生时间戳（含时区） |
| anomaly_type | VARCHAR(64) | 否 | - | 异常类型，枚举值见下方 |
| severity | VARCHAR(16) | 否 | - | 严重等级，枚举值见下方 |
| metric_name | VARCHAR(64) | 否 | - | 异常关联的指标名称 |
| metric_value | FLOAT | 否 | - | 异常发生时的实际指标值 |
| threshold_value | FLOAT | 否 | - | 对应阈值或期望值 |
| description | TEXT | 否 | - | 异常事件的详细描述 |
| resolved | BOOLEAN | 否 | - | 是否已处理，true 表示已解决 |
| detection_method | VARCHAR(32) | 否 | - | 检测方式，枚举值见下方 |

**anomaly_type 枚举值：**

| 值 | 说明 |
|---|---|
| energy_spike | 能耗突增 |
| low_cop | 低能效比 (COP) |
| temp_deviation | 温度偏差 |

**severity 枚举值：**

| 值 | 说明 |
|---|---|
| low | 低 - 信息级别，无需立即处理 |
| medium | 中 - 需关注，建议在计划维护时处理 |
| high | 高 - 需尽快处理，可能影响正常运行 |
| critical | 严重 - 需立即处理，影响安全或造成重大损失 |

**detection_method 枚举值：**

| 值 | 说明 |
|---|---|
| threshold | 基于阈值规则的检测 |
| ml_model | 基于机器学习模型的检测 |

---

## 6. 标准数据导入格式

当前后端实现支持两种能耗导入方式。

### 6.1 JSON Body 导入（`POST /api/v1/import/energy`）

请求体顶层字段为 `records`，每条记录都必须自带 `building_id`。

```json
{
  "records": [
    {
      "building_id": "BLD-001",
      "timestamp": "2026-03-09T08:00:00",
      "electricity_kwh": 120.5,
      "water_m3": 3.2,
      "gas_m3": 0.0,
      "hvac_kwh": 45.0,
      "hvac_supply_temp": 7.0,
      "hvac_return_temp": 12.0,
      "hvac_flow_rate": 50.0,
      "outdoor_temp": 18.5,
      "outdoor_humidity": 65.0,
      "occupancy_density": 0.05
    }
  ],
  "validate": true,
  "on_conflict": "skip"
}
```

### 6.2 文件上传导入（`POST /api/v1/import/upload`）

- 支持文件类型：`.csv`、`.json`
- CSV 编码：`UTF-8`（接口兼容带 BOM 的 `UTF-8-SIG`）
- CSV 首行必须是字段名，至少包含：`building_id`、`timestamp`
- `.json` 文件应为对象数组，每个对象字段与 `EnergyRecordCreate` 一致

CSV 示例（`energy_records.csv`）：

```csv
building_id,timestamp,electricity_kwh,water_m3,gas_m3,hvac_kwh,hvac_supply_temp,hvac_return_temp,hvac_flow_rate,outdoor_temp,outdoor_humidity,occupancy_density
BLD-001,2026-03-09T08:00:00,120.5,3.2,0.0,45.0,7.0,12.0,50.0,18.5,65.0,0.05
```

### 6.3 字段说明（单条能耗记录）

| 字段名 | 数据类型 | 是否必填 | 说明 |
|---|---|---|---|
| building_id | string | 是 | 建筑业务编号 |
| timestamp | string(datetime) | 是 | 采集时间，支持 ISO 8601 常见格式 |
| electricity_kwh | number | 否 | 电力消耗 (kWh)，>= 0 |
| water_m3 | number | 否 | 用水量 (m3)，>= 0 |
| gas_m3 | number | 否 | 燃气消耗 (m3)，>= 0 |
| hvac_kwh | number | 否 | 暖通空调能耗 (kWh)，>= 0 |
| hvac_supply_temp | number | 否 | 暖通空调供水温度 (C) |
| hvac_return_temp | number | 否 | 暖通空调回水温度 (C) |
| hvac_flow_rate | number | 否 | 暖通空调水流量 (m3/h)，>= 0 |
| outdoor_temp | number | 否 | 室外温度 (C) |
| outdoor_humidity | number | 否 | 室外相对湿度 (%) |
| occupancy_density | number | 否 | 人员密度，>= 0 |

### 6.4 导入行为说明（与当前实现一致）

- 校验通过后按行插入，返回 `ImportResult`。
- `on_conflict` 参数已定义在请求模型中，但当前服务层尚未实现 `update/error` 的差异化冲突处理。
- 上传接口仅解析能耗记录格式，设备/建筑 CSV 不能通过该接口导入。
