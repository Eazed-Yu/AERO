export interface WeatherRecord {
  id: number
  building_id: string
  timestamp: string
  dry_bulb_temp?: number
  wet_bulb_temp?: number
  relative_humidity?: number
  wind_speed?: number
  solar_radiation?: number
  atmospheric_pressure?: number
}
