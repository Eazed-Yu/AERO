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

系统接受以下 JSON 格式进行能耗记录的批量导入。每次请求的顶层结构为一个对象，包含 `building_id` 和 `records` 数组。

### 请求结构

```json
{
  "building_id": "BLD-001",
  "records": [
    {
      "timestamp": "2026-03-09T08:00:00+08:00",
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
    },
    {
      "timestamp": "2026-03-09T09:00:00+08:00",
      "electricity_kwh": 135.2,
      "water_m3": 3.5,
      "gas_m3": 0.0,
      "hvac_kwh": 52.3,
      "hvac_supply_temp": 7.0,
      "hvac_return_temp": 12.5,
      "hvac_flow_rate": 55.0,
      "outdoor_temp": 20.1,
      "outdoor_humidity": 60.0,
      "occupancy_density": 0.08
    }
  ]
}
```

### 字段说明

| 字段名 | 数据类型 | 是否必填 | 说明 |
|---|---|---|---|
| building_id | string | 是 | 建筑唯一业务编号，必须已存在于 buildings 表中 |
| records | array | 是 | 能耗记录数组，至少包含一条记录 |
| records[].timestamp | string (ISO 8601) | 是 | 数据采集时间，必须包含时区信息 |
| records[].electricity_kwh | number | 否 | 电力消耗 (kWh)，缺省时不更新该指标 |
| records[].water_m3 | number | 否 | 用水量 (m³)，缺省时不更新该指标 |
| records[].gas_m3 | number | 否 | 燃气消耗 (m³)，缺省时不更新该指标 |
| records[].hvac_kwh | number | 否 | 暖通空调能耗 (kWh)，缺省时不更新该指标 |
| records[].hvac_supply_temp | number | 否 | 暖通空调供水温度 (°C) |
| records[].hvac_return_temp | number | 否 | 暖通空调回水温度 (°C) |
| records[].hvac_flow_rate | number | 否 | 暖通空调水流量 (m³/h) |
| records[].outdoor_temp | number | 否 | 室外温度 (°C) |
| records[].outdoor_humidity | number | 否 | 室外相对湿度 (%) |
| records[].occupancy_density | number | 否 | 人员密度 (人/m²) |

### 导入规则

- **building_id** 必须对应 `buildings` 表中已存在的记录，否则导入失败。
- **timestamp** 必须符合 ISO 8601 格式，且必须携带时区偏移量（如 `+08:00`）或使用 UTC 标记 (`Z`)。
- 所有数值类型字段不得为负数（带有 `CHECK >= 0` 约束的字段）。
- 同一 `building_id` + `timestamp` 组合重复导入时，系统执行幂等覆盖（upsert）。
- 单次导入的 `records` 数组大小建议不超过 **1000** 条，超出时请分批提交。
