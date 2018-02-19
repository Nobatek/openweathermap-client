"""OpenWeatherMap API response schemas."""

import datetime as dt
import marshmallow as ma

from .utils import dt_from_timestamp


class CityCoordSchema(ma.Schema):
    """City geographical coordinates schema."""
    latitude = ma.fields.Float(load_from='lat')
    longitude = ma.fields.Float(load_from='lon')


class CitySchema(ma.Schema):
    """City schema."""
    id = ma.fields.Integer()
    name = ma.fields.String()
    country = ma.fields.String()  # country code (FR, GB, ...)
    coord = ma.fields.Nested(CityCoordSchema)


class MainDataSchema(ma.Schema):
    """Main weather data schema."""
    class Meta():
        exclude = ('temp_kf',)
    temp = ma.fields.Float()  # temperature, °C (if units=metric)
    temp_min = ma.fields.Float()  # minimum temperature, °C
    temp_max = ma.fields.Float()  # maximum temperature, °C
    humidity = ma.fields.Float()  # humidity, %
    pressure = ma.fields.Float()  # atmospheric pressure at sea level, hPa
    sea_level = ma.fields.Float()  # atmospheric pressure at sea level, hPa
    grnd_level = ma.fields.Float()  # atmospheric pressure at ground level, hPa


class WindDataSchema(ma.Schema):
    """Wind data schema."""
    direction = ma.fields.Float(load_from='deg')  # wind direction, degrees
    speed = ma.fields.Float()  # wind speed, meter/sec


class WeatherDataSchema(ma.Schema):
    """Weather data schema."""
    id = ma.fields.Integer()  # weather condition id
    main = ma.fields.String()  # groud of weather parameters (rain, snow, ...)
    description = ma.fields.String()  # wearther condition within the group
    icon = ma.fields.String()  # weather icon id


class CloudDataSchema(ma.Schema):
    """Cloud data schema."""
    clouds_all = ma.fields.Integer()  # cloudiness percentage, %


class RainDataSchema(ma.Schema):
    """Rain data schema."""
    rain_3h = ma.fields.Float()  # rain volume for the last 3 hours, mm


class SnowDataSchema(ma.Schema):
    """Snow data schema."""
    snow_3h = ma.fields.Float()  # snow volume for the last 3 hours


class ForecastDataSchema(ma.Schema):
    """Forecast data schema."""
    dt_value = ma.fields.Method(load_from='dt', deserialize='_from_ts')  # UTC
    dt_timestamp = ma.fields.Integer(load_from='dt')  # original UNIX timestamp
    dt_txt = ma.fields.String()
    main = ma.fields.Nested(MainDataSchema)
    weather = ma.fields.List(
        ma.fields.Nested(WeatherDataSchema)
    )
    clouds = ma.fields.Nested(CloudDataSchema)
    wind = ma.fields.Nested(WindDataSchema)
    rain = ma.fields.Nested(RainDataSchema)
    snow = ma.fields.Nested(SnowDataSchema)

    @staticmethod
    def _from_ts(timestamp):
        return dt_from_timestamp(timestamp, ts_tz=dt.timezone.utc)


class ForecastSchema(ma.Schema):
    """Forecast response schema."""
    city = ma.fields.Nested(CitySchema)
    cnt = ma.fields.Integer()
    datas = ma.fields.List(
        ma.fields.Nested(ForecastDataSchema),
        load_from='list'
    )


class CurrentWeatherSysDataSchema(ma.Schema):
    """Current weather sys data schema."""
    country = ma.fields.String()
    sunrise = ma.fields.Method(deserialize='_from_ts')  # UTC
    sunset = ma.fields.Method(deserialize='_from_ts')  # UTC
    sunrise_timestamp = ma.fields.Integer(load_from='sunrise')
    sunset_timestamp = ma.fields.Integer(load_from='sunset')

    @staticmethod
    def _from_ts(timestamp):
        return dt_from_timestamp(timestamp, ts_tz=dt.timezone.utc)


class CurrentWeatherSchema(ma.Schema):
    """Current weather response schema."""
    city_id = ma.fields.Integer(load_from='id')
    city_name = ma.fields.String(load_from='name')
    city_coord = ma.fields.Nested(
        CityCoordSchema,
        load_from='coord'
    )
    dt_value = ma.fields.Method(load_from='dt', deserialize='_from_ts')  # UTC
    dt_timestamp = ma.fields.Integer(load_from='dt')  # original UNIX timestamp
    main = ma.fields.Nested(MainDataSchema)
    weather = ma.fields.List(
        ma.fields.Nested(WeatherDataSchema)
    )
    clouds = ma.fields.Nested(CloudDataSchema)
    wind = ma.fields.Nested(WindDataSchema)
    rain = ma.fields.Nested(
        RainDataSchema,
        allow_none=True
    )
    snow = ma.fields.Nested(
        SnowDataSchema,
        allow_none=True
    )
    sys = ma.fields.Nested(CurrentWeatherSysDataSchema)

    @staticmethod
    def _from_ts(timestamp):
        return dt_from_timestamp(timestamp, ts_tz=dt.timezone.utc)


class CurrentWeatherSearchSchema(ma.Schema):
    """Current weather response schema for within box, within circle
    and search for IDs."""
    status_code = ma.fields.Integer(load_from='cod')
    calc_time = ma.fields.Float()
    cnt = ma.fields.Integer()
    datas = ma.fields.List(
        ma.fields.Nested(CurrentWeatherSchema),
        load_from='list'
    )


class UVIndexSchema(ma.Schema):
    """Current UV index response schema."""
    latitude = ma.fields.Float(load_from='lat')
    longitude = ma.fields.Float(load_from='lon')
    date = ma.fields.DateTime(
        load_from='date_iso', deserialize='_from_iso8601')
    date_iso = ma.fields.String()  # original ISO 8601 datetime
    dt_timestamp = ma.fields.Integer(load_from='date')  # timestamp ISO 8601
    value = ma.fields.Float()  # UV index

    @staticmethod
    def _from_iso8601(date):
        return ma.utils.from_iso_datetime(date)


class AirPollutionLocationSchema(ma.Schema):
    """Air pollution location data schema."""
    latitude = ma.fields.Float()
    longitude = ma.fields.Float()


class AirPollutionBaseSchema(ma.Schema):
    """Air pollution base response schema."""
    time = ma.fields.DateTime(deserialize='_from_iso8601')
    # original ISO 8601 timestamp
    time_iso8601 = ma.fields.String(load_from='time')
    location = ma.fields.Nested(AirPollutionLocationSchema)

    @staticmethod
    def _from_iso8601(time):
        return ma.utils.from_iso_datetime(time)


class AirPollutionCarbonMonoxydeDataSchema(ma.Schema):
    """Air pollution carbon monoxyde data schema."""
    precision = ma.fields.Float()  # measurement precision
    pressure = ma.fields.Float()  # atmospheric pressure, hPa
    value = ma.fields.Float()  # carbon monoxide volume mixing ratio


class AirPollutionCarbonMonoxydeSchema(AirPollutionBaseSchema):
    """Air pollution carbon monoxyde response schema."""
    datas = ma.fields.List(
        ma.fields.Nested(AirPollutionCarbonMonoxydeDataSchema),
        load_from='data'
    )


class AirPollutionOzoneSchema(AirPollutionBaseSchema):
    """Air pollution ozone response schema."""
    data = ma.fields.Float()  # ozone layer thickness, DU (Dobson Unit)


class AirPollutionSulfurDioxideDataSchema(ma.Schema):
    """Air pollution sulfur dioxide data schema."""
    precision = ma.fields.Float()  # measurement precision
    pressure = ma.fields.Float()  # atmospheric pressure, hPa
    value = ma.fields.Float()  # sulfur dioxide volume mixing ratio


class AirPollutionSulfurDioxideSchema(AirPollutionBaseSchema):
    """Air pollution sulfur dioxide response schema."""
    datas = ma.fields.List(
        ma.fields.Nested(AirPollutionSulfurDioxideDataSchema),
        load_from='data'
    )


class AirPollutionNitrogenDioxideItemDataSchema(ma.Schema):
    """Air pollution nitrogen dioxide item data schema."""
    precision = ma.fields.Float()  # measurement precision
    value = ma.fields.Float()  # nitrogen dioxide volume mixing ratio


class AirPollutionNitrogenDioxideItemSchema(ma.Schema):
    """Air pollution nitrogen dioxide item schema."""
    no2 = ma.fields.Nested(AirPollutionNitrogenDioxideItemDataSchema)
    no2_strat = ma.fields.Nested(AirPollutionNitrogenDioxideItemDataSchema)
    no2_trop = ma.fields.Nested(AirPollutionNitrogenDioxideItemDataSchema)


class AirPollutionNitrogenDioxideSchema(AirPollutionBaseSchema):
    """Air pollution nitrogen dioxide response schema."""
    data = ma.fields.Nested(AirPollutionNitrogenDioxideItemSchema)
