-- AERO Database Schema (PostgreSQL)
-- 引入区域实体，层级: Region → Building → Equipment


DROP TABLE IF EXISTS cooling_tower_records CASCADE;
DROP TABLE IF EXISTS pump_records CASCADE;
DROP TABLE IF EXISTS vav_records CASCADE;
DROP TABLE IF EXISTS boiler_records CASCADE;
DROP TABLE IF EXISTS ahu_records CASCADE;
DROP TABLE IF EXISTS chiller_records CASCADE;
DROP TABLE IF EXISTS anomaly_events CASCADE;
DROP TABLE IF EXISTS energy_meters CASCADE;
DROP TABLE IF EXISTS weather_records CASCADE;
DROP TABLE IF EXISTS equipment CASCADE;
DROP TABLE IF EXISTS buildings CASCADE;
DROP TABLE IF EXISTS regions CASCADE;

-- ============================================================
-- 1. regions (区域)
-- ============================================================
CREATE TABLE regions (
    id           VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    region_id    VARCHAR(64)  NOT NULL UNIQUE,
    name         VARCHAR(255) NOT NULL,
    description  TEXT,
    address      VARCHAR(512),
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 2. buildings (建筑，属于区域)
-- ============================================================
CREATE TABLE buildings (
    id                   VARCHAR(36)       PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    building_id          VARCHAR(64)       NOT NULL UNIQUE,
    region_id            VARCHAR(64)       NOT NULL,
    name                 VARCHAR(255)      NOT NULL,
    building_type        VARCHAR(64)       NOT NULL,
    area                 DOUBLE PRECISION  NOT NULL CHECK (area > 0),
    address              VARCHAR(512),
    floors               INTEGER,
    year_built           INTEGER,
    climate_zone         VARCHAR(32),
    cooling_area         DOUBLE PRECISION,
    design_cooling_load  DOUBLE PRECISION,
    design_heating_load  DOUBLE PRECISION,
    created_at           TIMESTAMP         NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP         NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_building_region ON buildings(region_id);
CREATE INDEX idx_building_type ON buildings(building_type);

-- ============================================================
-- 3. equipment (设备，必须属于区域，可选属于建筑)
-- ============================================================
CREATE TABLE equipment (
    id              VARCHAR(36)       PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    region_id       VARCHAR(64)       NOT NULL,
    building_id     VARCHAR(64),
    device_id       VARCHAR(128)      NOT NULL UNIQUE,
    device_name     VARCHAR(255)      NOT NULL,
    device_type     VARCHAR(64)       NOT NULL,
    system_type     VARCHAR(32),
    model           VARCHAR(128),
    manufacturer    VARCHAR(128),
    rated_power_kw  DOUBLE PRECISION,
    rated_capacity  DOUBLE PRECISION,
    rated_cop       DOUBLE PRECISION,
    location        VARCHAR(255),
    install_date    DATE,
    status          VARCHAR(32)       DEFAULT 'active',
    created_at      TIMESTAMP         NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP         NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_equipment_region ON equipment(region_id);
CREATE INDEX idx_equipment_building ON equipment(building_id);
CREATE INDEX idx_equipment_type ON equipment(device_type);

-- ============================================================
-- 4. weather_records (气象记录，按区域)
-- ============================================================
CREATE TABLE weather_records (
    id                    SERIAL            PRIMARY KEY,
    region_id             VARCHAR(64)       NOT NULL,
    timestamp             TIMESTAMP         NOT NULL,
    dry_bulb_temp         DOUBLE PRECISION,
    wet_bulb_temp         DOUBLE PRECISION,
    relative_humidity     DOUBLE PRECISION,
    wind_speed            DOUBLE PRECISION,
    solar_radiation       DOUBLE PRECISION,
    atmospheric_pressure  DOUBLE PRECISION
);
CREATE INDEX idx_weather_region_time ON weather_records(region_id, timestamp);

-- ============================================================
-- 5. energy_meters (能耗表，建筑级，附 region_id)
-- ============================================================
CREATE TABLE energy_meters (
    id                      SERIAL            PRIMARY KEY,
    region_id               VARCHAR(64)       NOT NULL,
    building_id             VARCHAR(64)       NOT NULL,
    timestamp               TIMESTAMP         NOT NULL,
    total_electricity_kwh   DOUBLE PRECISION,
    hvac_electricity_kwh    DOUBLE PRECISION,
    lighting_kwh            DOUBLE PRECISION,
    plug_load_kwh           DOUBLE PRECISION,
    peak_demand_kw          DOUBLE PRECISION,
    gas_m3                  DOUBLE PRECISION,
    water_m3                DOUBLE PRECISION,
    cooling_kwh             DOUBLE PRECISION,
    heating_kwh             DOUBLE PRECISION
);
CREATE INDEX idx_energy_meter_region ON energy_meters(region_id);
CREATE INDEX idx_energy_meter_building_time ON energy_meters(building_id, timestamp);

-- ============================================================
-- 6. chiller_records
-- ============================================================
CREATE TABLE chiller_records (
    id                  SERIAL PRIMARY KEY,
    device_id           VARCHAR(128) NOT NULL,
    timestamp           TIMESTAMP    NOT NULL,
    chw_supply_temp     DOUBLE PRECISION,
    chw_return_temp     DOUBLE PRECISION,
    chw_flow_rate       DOUBLE PRECISION,
    cw_supply_temp      DOUBLE PRECISION,
    cw_return_temp      DOUBLE PRECISION,
    cw_flow_rate        DOUBLE PRECISION,
    power_kw            DOUBLE PRECISION,
    cooling_capacity_kw DOUBLE PRECISION,
    load_ratio          DOUBLE PRECISION,
    cop                 DOUBLE PRECISION,
    evaporator_approach DOUBLE PRECISION,
    condenser_approach  DOUBLE PRECISION,
    compressor_rla_pct  DOUBLE PRECISION,
    running_status      VARCHAR(16)
);
CREATE INDEX idx_chiller_device_time ON chiller_records(device_id, timestamp);

-- ============================================================
-- 7. ahu_records
-- ============================================================
CREATE TABLE ahu_records (
    id                   SERIAL PRIMARY KEY,
    device_id            VARCHAR(128) NOT NULL,
    timestamp            TIMESTAMP    NOT NULL,
    supply_air_temp      DOUBLE PRECISION,
    return_air_temp      DOUBLE PRECISION,
    mixed_air_temp       DOUBLE PRECISION,
    outdoor_air_temp     DOUBLE PRECISION,
    supply_air_humidity  DOUBLE PRECISION,
    return_air_humidity  DOUBLE PRECISION,
    supply_fan_speed     DOUBLE PRECISION,
    supply_fan_power_kw  DOUBLE PRECISION,
    supply_air_flow      DOUBLE PRECISION,
    return_fan_speed     DOUBLE PRECISION,
    chw_valve_pos        DOUBLE PRECISION,
    hw_valve_pos         DOUBLE PRECISION,
    oa_damper_pos        DOUBLE PRECISION,
    ra_damper_pos        DOUBLE PRECISION,
    duct_static_pressure DOUBLE PRECISION,
    filter_dp            DOUBLE PRECISION,
    operating_mode       VARCHAR(16),
    sat_setpoint         DOUBLE PRECISION,
    dsp_setpoint         DOUBLE PRECISION,
    running_status       VARCHAR(16)
);
CREATE INDEX idx_ahu_device_time ON ahu_records(device_id, timestamp);

-- ============================================================
-- 8. boiler_records
-- ============================================================
CREATE TABLE boiler_records (
    id                  SERIAL PRIMARY KEY,
    device_id           VARCHAR(128) NOT NULL,
    timestamp           TIMESTAMP    NOT NULL,
    hw_supply_temp      DOUBLE PRECISION,
    hw_return_temp      DOUBLE PRECISION,
    hw_flow_rate        DOUBLE PRECISION,
    firing_rate         DOUBLE PRECISION,
    power_kw            DOUBLE PRECISION,
    fuel_consumption    DOUBLE PRECISION,
    heating_capacity_kw DOUBLE PRECISION,
    efficiency          DOUBLE PRECISION,
    flue_gas_temp       DOUBLE PRECISION,
    running_status      VARCHAR(16)
);
CREATE INDEX idx_boiler_device_time ON boiler_records(device_id, timestamp);

-- ============================================================
-- 9. vav_records
-- ============================================================
CREATE TABLE vav_records (
    id                     SERIAL PRIMARY KEY,
    device_id              VARCHAR(128) NOT NULL,
    timestamp              TIMESTAMP    NOT NULL,
    zone_temp              DOUBLE PRECISION,
    zone_temp_setpoint_clg DOUBLE PRECISION,
    zone_temp_setpoint_htg DOUBLE PRECISION,
    airflow                DOUBLE PRECISION,
    airflow_setpoint       DOUBLE PRECISION,
    damper_pos             DOUBLE PRECISION,
    discharge_air_temp     DOUBLE PRECISION,
    reheat_valve_pos       DOUBLE PRECISION,
    zone_co2               DOUBLE PRECISION,
    occupancy_status       VARCHAR(16),
    operating_mode         VARCHAR(16)
);
CREATE INDEX idx_vav_device_time ON vav_records(device_id, timestamp);

-- ============================================================
-- 10. pump_records
-- ============================================================
CREATE TABLE pump_records (
    id                    SERIAL PRIMARY KEY,
    device_id             VARCHAR(128) NOT NULL,
    timestamp             TIMESTAMP    NOT NULL,
    speed                 DOUBLE PRECISION,
    power_kw              DOUBLE PRECISION,
    flow_rate             DOUBLE PRECISION,
    inlet_pressure        DOUBLE PRECISION,
    outlet_pressure       DOUBLE PRECISION,
    differential_pressure DOUBLE PRECISION,
    running_status        VARCHAR(16)
);
CREATE INDEX idx_pump_device_time ON pump_records(device_id, timestamp);

-- ============================================================
-- 11. cooling_tower_records
-- ============================================================
CREATE TABLE cooling_tower_records (
    id              SERIAL PRIMARY KEY,
    device_id       VARCHAR(128) NOT NULL,
    timestamp       TIMESTAMP    NOT NULL,
    fan_speed       DOUBLE PRECISION,
    fan_power_kw    DOUBLE PRECISION,
    cw_inlet_temp   DOUBLE PRECISION,
    cw_outlet_temp  DOUBLE PRECISION,
    wet_bulb_temp   DOUBLE PRECISION,
    approach        DOUBLE PRECISION,
    range           DOUBLE PRECISION,
    running_status  VARCHAR(16)
);
CREATE INDEX idx_ct_device_time ON cooling_tower_records(device_id, timestamp);

-- ============================================================
-- 12. anomaly_events
-- ============================================================
CREATE TABLE anomaly_events (
    id                 VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    region_id          VARCHAR(64)  NOT NULL,
    building_id        VARCHAR(64),
    device_id          VARCHAR(128),
    timestamp          TIMESTAMP    NOT NULL,
    anomaly_type       VARCHAR(64)  NOT NULL,
    severity           VARCHAR(16)  NOT NULL,
    metric_name        VARCHAR(64)  NOT NULL,
    metric_value       DOUBLE PRECISION NOT NULL,
    threshold_value    DOUBLE PRECISION,
    description        TEXT         NOT NULL,
    resolved           BOOLEAN      NOT NULL DEFAULT FALSE,
    detection_method   VARCHAR(32)  NOT NULL DEFAULT 'threshold',
    equipment_type     VARCHAR(32),
    fault_code         VARCHAR(32),
    recommended_action TEXT,
    created_at         TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_anomaly_region_time ON anomaly_events(region_id, timestamp);
CREATE INDEX idx_anomaly_severity    ON anomaly_events(severity, resolved);
