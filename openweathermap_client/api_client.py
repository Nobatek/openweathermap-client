"""A client for Open Weather Map API.

See documentaiton: https://openweathermap.org/api
How to start: https://openweathermap.org/appid
5 days weather forecast: https://openweathermap.org/forecast5
current weather: https://openweathermap.org/current
air pollution:
https://openweathermap.org/api/pollution/co,
https://openweathermap.org/api/pollution/o3,
https://openweathermap.org/api/pollution/so2,
https://openweathermap.org/api/pollution/no2
"""

import logging
from io import StringIO
import zlib
import json
from collections import OrderedDict
from urllib.parse import urljoin
import requests
import marshmallow as ma

from . import _LOGGER_NAME
from .schemas import (
    ForecastSchema, CurrentWeatherSchema, CurrentWeatherSearchSchema,
    UVIndexSchema,
    AirPollutionCarbonMonoxydeSchema, AirPollutionOzoneSchema,
    AirPollutionSulfurDioxideSchema, AirPollutionNitrogenDioxideSchema,
    CitySchema)
from .exceptions import (
    OpenWeatherMapClientError, OWMClientKeyNotDefinedError,
    OWMClientUnknownServiceNameError, OWMClientAccessLimitationError,
    OWMClientValidationError)


_API_HOST = 'api.openweathermap.org'
_API_DATA_VERSION = '2.5'
_API_POLLUTION_VERSION = 'v1'


logger = logging.getLogger(_LOGGER_NAME)


class OpenWeatherMapClient():
    """OpenWeatherMap API client class."""

    _AVAILABLE_SERVICES = {
        'city_list': {
            # url list taken from https://openweathermap.org/appid#work
            'uri': 'http://bulk.openweathermap.org/sample/city.list.json.gz',
            'schema': {'name': CitySchema, 'many': True},
            'description': 'Cities\' IDs list.'},
        'forecast_5d': {
            'uri': '/data/{v}/forecast'.format(v=_API_DATA_VERSION),
            'schema': {'name': ForecastSchema, 'many': False},
            'description': 'Forecast 5 day / 3 hour for a location.'},
        'current_weather': {
            'uri': '/data/{v}/weather'.format(v=_API_DATA_VERSION),
            'schema': {'name': CurrentWeatherSchema, 'many': False},
            'description': 'Current weather for a location.'},
        'current_weather_box': {
            'uri': '/data/{v}/box/city'.format(v=_API_DATA_VERSION),
            'schema': {'name': CurrentWeatherSearchSchema, 'many': False},
            'description': 'Current weather within a geographical box.'},
        'current_weather_circle': {
            'uri': '/data/{v}/find'.format(v=_API_DATA_VERSION),
            'schema': {'name': CurrentWeatherSearchSchema, 'many': False},
            'description': 'Current weather within a geographical circle.'},
        'current_weather_group': {
            'uri': '/data/{v}/group'.format(v=_API_DATA_VERSION),
            'schema': {'name': CurrentWeatherSearchSchema, 'many': False},
            'description': 'Current weather for a group of cities.'},
        'air_pollution_carbon_monoxyde': {
            'uri': '/pollution/{v}/co/'.format(v=_API_POLLUTION_VERSION),
            'schema': {
                'name': AirPollutionCarbonMonoxydeSchema, 'many': False},
            'description': 'Carbon monoxyde for a location and time.'},
        'air_pollution_ozone': {
            'uri': '/pollution/{v}/o3/'.format(v=_API_POLLUTION_VERSION),
            'schema': {'name': AirPollutionOzoneSchema, 'many': False},
            'description': 'Ozone for a location and time.'},
        'air_pollution_sulfur_dioxide': {
            'uri': '/pollution/{v}/so2/'.format(v=_API_POLLUTION_VERSION),
            'schema': {'name': AirPollutionSulfurDioxideSchema, 'many': False},
            'description': 'Sulfur dioxide for a location and time.'},
        'air_pollution_nitrogen_dioxide': {
            'uri': '/pollution/{v}/no2/'.format(v=_API_POLLUTION_VERSION),
            'schema': {
                'name': AirPollutionNitrogenDioxideSchema, 'many': False},
            'description': 'Nitrogen dioxide for a location and time.'},
        'uv_index_current': {
            'uri': '/data/{v}/uvi'.format(v=_API_DATA_VERSION),
            'schema': {'name': UVIndexSchema, 'many': False},
            'description': 'UV index for a location.'},
        'uv_index_forecast': {
            'uri': '/data/{v}/uvi/forecast'.format(v=_API_DATA_VERSION),
            'schema': {'name': UVIndexSchema, 'many': True},
            'description': 'Forecast UV index for a location.'},
        'uv_index_historical': {
            'uri': '/data/{v}/uvi/history'.format(v=_API_DATA_VERSION),
            'schema': {'name': UVIndexSchema, 'many': True},
            'description': 'Historical UV index for a location.'},
    }

    def __init__(
            self, api_key, *, use_ssl=True, host=_API_HOST, max_retries=5,
            units='metric'):
        """
        :param str api_key: API key used to call the API.
        :param bool use_ssl: (optional, default True)
        :param str host: (optional, default api.openweathermap.org)
            Server host name of the API.
        :param int max_retries: (optional, default 5)
            Number max of retries if errors occured while calling the API.
        :param str units: (optional, default metric)
            Units format. standard, metric, and imperial units are available.
            See https://openweathermap.org/weather-data
        """
        if api_key is None:
            raise OWMClientKeyNotDefinedError()

        self.api_key = api_key
        self.host = host or _API_HOST
        self.max_retries = max_retries
        self.units = units

        self._base_uri = 'http{ssl}://{host}'.format(
            ssl='s' if use_ssl else '', host=self.host)
        self._base_uri_params = {
            'appid': self.api_key,
            'units': self.units,
        }

        self.last_uri_call = None
        self.last_uri_call_tries = 0

        logger.debug(
            'OpenWeatherMap API client initialized. Host: %s', self.host)

    def __repr__(self):
        return (
            '<{self.__class__.__name__}('
            'api_key="{self.api_key}"'
            ', base_uri={self._base_uri}'
            ', max_retries={self.max_retries}'
            ')>'.format(self=self))

    @property
    def available_services(self):
        """List all available services (implemented calls of API endpoints)."""
        return self._AVAILABLE_SERVICES

    def _get(self, uri, **kwargs):
        """Send a GET request, using max retries if call failed.

        ..Note:
            last_uri_call and last_uri_call_tries are defined in this method.

        :returns requests.models.Response:
        :raises OpenWeatherMapClientError:
            When a request connection error or timeout is thrown.
        :raises OWMClientAccessLimitationError:
            When the OpenWeatherMap's limit of calls per minute is reached.
        :raises requests.exceptions.HTTPError:
            When response status code is not OK (and max retries reached).
        """
        # build a human readable uri with query parameters
        self.last_uri_call = '?'.join([
            uri, '&'.join([
                '{}={}'.format(k, v if k != 'appid' else 'XxX')
                for k, v in kwargs.get('params', {}).items()])
        ])
        self.last_uri_call_tries = 0

        is_success = False
        while not is_success and self.last_uri_call_tries < self.max_retries:
            self.last_uri_call_tries += 1
            try:
                # send request and receive response
                response = requests.get(uri, **kwargs)
            except (requests.ConnectionError, requests.Timeout,) as src_exc:
                logger.warning(
                    '%i/%i GET %s: %s', self.last_uri_call_tries,
                    self.max_retries, self.last_uri_call, src_exc)
                response = None
                if self.last_uri_call_tries >= self.max_retries:
                    exc = OpenWeatherMapClientError(str(src_exc))
                    logger.error('GET %s: %s', self.last_uri_call, exc)
                    raise exc

            if response is not None:
                # is response ok (200) ?
                if response.status_code != requests.codes.ok:
                    if self.last_uri_call_tries >= self.max_retries:
                        # is response a bad gateway (502) code ?
                        if response.status_code == requests.codes.bad_gateway:
                            limit_exc = OWMClientAccessLimitationError(
                                'For example, OpenWeatherMap free edition only'
                                'allows 60 API calls per minute!')
                            logger.error(
                                'GET %s: %s', self.last_uri_call, limit_exc)
                            raise limit_exc
                        response.raise_for_status()
                # no exception at all...
                elif self.last_uri_call_tries < self.max_retries:
                    is_success = True

        return response

    def _get_data(self, service_name, *, extra_uri=None, params=None,
                  with_units=True):
        """Send GET request to retrieve data from a service.

        :param str service_name:
            The service name to call. See available_services property.
        :param str extra_uri: (optional, default None)
        :param dict params: (optional, default None)
            The query parameters to pass in request.
        """
        if service_name not in self._AVAILABLE_SERVICES.keys():
            exc_serv = OWMClientUnknownServiceNameError(
                'Invalid service name: {}. Available services are: {}'.format(
                    service_name, ', '.join(self._AVAILABLE_SERVICES.keys())))
            logger.error(str(exc_serv))
            raise exc_serv

        # get service information (uri, schema, ...)
        service_info = self._AVAILABLE_SERVICES[service_name]

        # build uri
        uri = urljoin(self._base_uri, service_info['uri'])
        if extra_uri is not None:
            uri = urljoin(uri, extra_uri)

        # prepare query parameters
        query_params = params or OrderedDict()
        query_params.update(self._base_uri_params)
        if not with_units:
            query_params.pop('units')
        # send request and receive response
        response = self._get(uri, params=query_params)

        # default response format is JSON and this is great !
        resp_data = response.json()

        # is resp_data an error ?
        if 'error' in resp_data:
            exc = OpenWeatherMapClientError('{} on GET {}'.format(
                resp_data['error'], self.last_uri_call))
            logger.error(str(exc))
            raise exc

        # deserialize API response
        return self._deserialize_with_schema(service_info['schema'], resp_data)

    @staticmethod
    def _deserialize_with_schema(data_schema_info, json_data):
        """Use a marshmallow schema to deserialize JSON data."""
        data_schema = data_schema_info['name'](many=data_schema_info['many'])
        try:
            # validate and deserialized data
            return data_schema.load(json_data)[0]
        except ma.ValidationError as src_exc:
            exc = OWMClientValidationError(str(src_exc))
            logger.error(str(exc))
            raise exc

    def get_city_list(self, *, validate_with_schema=True):
        """Retrieve all cities information, including cities' IDs list.
        In fact, there is more data than only IDs (names, coordinates...).

        A JSON compressed file is downloaded and serialized as objects.

        ..Note:
            Use API by city ID (instead of city name, city coordinates or
            zip code) allows to get precise respond exactly for a city.

        :param bool validate_with_schema: (optional, default True)
            If False, raw JSON data is returned (as it is in the source file).
            If True, a marshmallow schema validates and format data on load.
            The first case is much faster, but in the second case some
            conversion is done (for example timestamps to datetimes).
        """
        # get service information (uri, schema, ...)
        service_name = 'city_list'
        service_info = self._AVAILABLE_SERVICES[service_name]

        # send request and receive response
        response = self._get(service_info['uri'], stream=True)

        # decompress downloaded file data
        zlib_obj = zlib.decompressobj(16 + zlib.MAX_WBITS)
        response_data = str(zlib_obj.decompress(response.content), 'utf-8')

        # create a stream with the string response and load JSON data
        io_data = StringIO(response_data)
        json_data = json.load(io_data)

        if not validate_with_schema:
            return json_data

        # deserialize API response into a marshmallow schema
        return self._deserialize_with_schema(service_info['schema'], json_data)

    def get_forecast_by_city_id(self, city_id):
        """Search for weather forecast (5 day / 3 hour) by city id.

        :param str city_id: The ID of the city to watch.
        """
        query_params = {'id': city_id}
        return self._get_data('forecast_5d', params=query_params)

    def get_forecast_by_coord(self, latitude, longitude):
        """Search for weather forecast (5 day / 3 hour) by city geographical
        coordinates.

        :param float latitude: The latitude coordinate of the city to watch.
        :param float longitude: The longitude coordinate of the city to watch.
        """
        query_params = {'lat': latitude, 'lon': longitude}
        return self._get_data('forecast_5d', params=query_params)

    def get_forecast_by_city_name(
            self, city_name, *, country_code=None, search_type=None):
        """Search for weather forecast (5 day / 3 hour) by city name and
        country code (ISO 3166).

        :param str country_code: (optional, default None)
            ISO 3166 country code of the city to watch, can be used for better
            search accuracy.
        :param str search_type: (optional, default None)
            City name search precision: 'None',
                'like' to get close city name result,
                'accurate' to get exact match city name result.
        :raises ValueError: When search_type value is invalid.
        """
        query_params = {'q': city_name}
        if country_code is not None:
            query_params['q'] = '{},{}'.format(city_name, country_code)
        if search_type in (None, 'like', 'accurate',):
            if search_type is not None:
                query_params.update({'type': search_type})
        else:
            exc = ValueError(
                'Invalid search_type: {}. Expected are: None/like/accurate.'
                .format(search_type))
            logger.warning(str(exc))
            raise exc
        return self._get_data('forecast_5d', params=query_params)

    def get_forecast_by_zip_code(self, zip_code, country_code):
        """Search for weather forecast (5 day / 3 hour) by city zip code and
        country code (ISO 3166).

        :param str zip_code: The zip code of the city to watch.
        :param str country_code: ISO 3166 country code of the city to watch.
        """
        query_params = {'zip': '{},{}'.format(zip_code, country_code)}
        return self._get_data('forecast_5d', params=query_params)

    def get_current_weather_by_city_id(self, city_id):
        """Retrieve current weather data by city id.

        :param str city_id: The ID of the city to watch.
        """
        return self._get_data('current_weather', params={'id': city_id})

    def get_current_weather_by_coord(self, latitude, longitude):
        """Retrieve current weather data by city geographical coordinates.

        :param float latitude: The latitude coordinate of the city to watch.
        :param float longitude: The longitude coordinate of the city to watch.
        """
        query_params = {'lat': latitude, 'lon': longitude}
        return self._get_data('current_weather', params=query_params)

    def get_current_weather_by_city_name(
            self, city_name, *, country_code=None, search_type=None):
        """Retrieve current weather data by city name and ISO 3166 country code.

        :param str country_code: (optional, default None)
            ISO 3166 country code of the city to watch, used for better search
            accuracy.
        :param str search_type: (optional, default None)
            City name search precision: 'None',
                'like' to get close city name result,
                'accurate' to get exact match city name result.
        :raises ValueError: When search_type value is invalid.
        """
        query_params = {'q': city_name}
        if country_code is not None:
            query_params['q'] = '{},{}'.format(city_name, country_code)
        if search_type in (None, 'like', 'accurate',):
            if search_type is not None:
                query_params.update({'type': search_type})
        else:
            exc = ValueError(
                'Invalid search_type: {}. Expected are: None/like/accurate.'
                .format(search_type))
            logger.warning(str(exc))
            raise exc
        return self._get_data('current_weather', params=query_params)

    def get_current_weather_by_zip_code(self, zip_code, country_code):
        """Retrieve current weather by city zip code and ISO 3166 country code.

        :param str zip_code: The zip code of the city to watch.
        :param str country_code: ISO 3166 country code of the city to watch.
        """
        query_params = {'zip': '{},{}'.format(zip_code, country_code)}
        return self._get_data('current_weather', params=query_params)

    def get_current_weather_within_box(
            self, box, zoom, *, cluster=None, lang=None):
        """Retrieve current weather within a rectangle zone (geographical
        coordinates of the box).

        :param list box: List of the 4 vertices coordinates of the box.
            [left_longitude, bottom_latitude, right_longitude, top_latitude]
        :param float zoom: Value of the zoom in the box.
        :param str cluster: (optional, default None)
            Use server clustering of points: 'None', 'yes' or 'no'.
        :param str lang: (optional, default None) Language to use.
        :raises ValueError: When box or cluster value is invalid.
        """
        if len(box) != 4:
            exc = ValueError('Invalid box: {}'.format(box))
            logger.warning(str(exc))
            raise exc
        box.extend([zoom])
        query_params = {'bbox': ','.join([str(coord) for coord in box])}
        if cluster in (None, 'yes', 'no',):
            if cluster is not None:
                query_params.update({'cluster': cluster})
        else:
            exc = ValueError('Invalid cluster: {}. Expected are: None/yes/no.'
                             .format(cluster))
            logger.warning(str(exc))
            raise exc
        if lang is not None:
            query_params.update({'lang': lang})
        return self._get_data('current_weather_box', params=query_params)

    def get_current_weather_within_circle(
            self, latitude, longitude, *, cluster=None, cnt=10, lang=None):
        """Retrieve current weather within a circle (geographical coordinates
        of the center point).

        :param float latitude:
            Latitude coordinate of the circle's center point.
        :param float longitude:
            Longitude coordinate of the circle's center point.
        :param str cluster: (optional, default None)
            Use server clustering of points: 'None', 'yes' or 'no'.
        :param int cnt: (optional, default 10, maximum 50)
            Expected number of cities around the point that should be returned.
        :param str lang: (optional, default None) Language to use.
        :raises ValueError: When cluster value is invalid.
        """
        query_params = {'lat': latitude, 'lon': longitude}
        query_params['cnt'] = max(0, min(cnt, 50))
        if cluster in (None, 'yes', 'no',):
            if cluster is not None:
                query_params.update({'cluster': cluster})
        else:
            exc = ValueError('Invalid cluster: {}. Expected are: None/yes/no.'
                             .format(cluster))
            logger.warning(str(exc))
            raise exc
        if lang is not None:
            query_params.update({'lang': lang})
        return self._get_data('current_weather_circle', params=query_params)

    def get_current_weather_group(self, city_ids):
        """Retrieve current weather for a group of city IDs.

        ..Note:
            A single city ID counts as a one API call!
            So if 3 IDs are given, this will be considered as a 3 API calls.

        :param list city_ids: List of the city IDs to search. Limited to 20.
        :raises ValueError: When city_ids list is over 20.
        """
        if len(city_ids) > 20:
            exc = ValueError('The limit of locations is 20.')
            logger.warning(str(exc))
            raise exc
        query_params = {'id': ','.join([str(cur_id) for cur_id in city_ids])}
        return self._get_data('current_weather_group', params=query_params)

    def get_air_pollution_carbon_monoxyde(
            self, latitude, longitude, *, datetime='current'):
        """Retrieve Carbon Monoxide index.

        ..Notes:

            Location format:
            Accuracy of coordinates affects maximum distance for search among
            available data entries around specified location.
            More digits beyond decimal point means shorter search distance.
                No decimal part: ~78km
                1 digit: 7862 m
                2 digits: 786 m
                3 digits: 78 m
                4 digits: 8 m
                5 digits: 1 m

            Date/time format: ISO 8601
            Searches for the latest available point within specified date.
                - 'current' searches
                    for the latest available data point up until now
                - 2016-01-02T15:04:05Z searches
                    between 2016-01-02T15:04:05Z and 2016-01-02T15:04:05.9999Z
                - 2016-01-02T15:04Z searches
                    between 2016-01-02T15:04:00Z and 2016-01-02T15:04:59.9999Z
                - 2016-01-02T15Z searches
                    between 2016-01-02T15:00:00Z and 2016-01-02T15:59:59.9999Z
                - 2016-01-02Z searches
                    between 2016-01-02T00:00:00Z and 2016-01-02T23:59:59.9999Z
                - 2016-01Z searches
                    between 2016-01-01T00:00:00Z and 2016-12-31T23:59:59.9999Z
                - 2016Z searches
                    between 2016-01-01T00:00:00Z and 2016-12-31T23:59:99.9999Z

        :param float latitude: Latitude coordinate of location.
        :param float longitude: Longitude coordinate of location.
        :param str datetime: (optional, default 'current')
            ISO 8601 date (UTC time) or alias ('current').
        """
        extra_uri = '{},{}/{}.json'.format(latitude, longitude, datetime)
        return self._get_data(
            'air_pollution_carbon_monoxyde', extra_uri=extra_uri)

    def get_air_pollution_ozone(
            self, latitude, longitude, *, datetime='current'):
        """Retrieve Ozone data.

        ..Notes:
            cf. 'get_air_pollution_carbon_monoxyde' method

        :param float latitude: Latitude coordinate of location.
        :param float longitude: Longitude coordinate of location.
        :param str datetime: (optional, default 'current')
            ISO 8601 date (UTC time) or alias ('current').
        """
        extra_uri = '{},{}/{}.json'.format(latitude, longitude, datetime)
        return self._get_data('air_pollution_ozone', extra_uri=extra_uri)

    def get_air_pollution_sulfur_dioxide(
            self, latitude, longitude, *, datetime='current'):
        """Retrieve Sulfur Dioxide index.

        ..Notes:
            cf. 'get_air_pollution_carbon_monoxyde' method

        :param float latitude: Latitude coordinate of location.
        :param float longitude: Longitude coordinate of location.
        :param str datetime: (optional, default 'current')
            ISO 8601 date (UTC time) or alias ('current').
        """
        extra_uri = '{},{}/{}.json'.format(latitude, longitude, datetime)
        return self._get_data(
            'air_pollution_sulfur_dioxide', extra_uri=extra_uri)

    def get_air_pollution_nitrogen_dioxide(
            self, latitude, longitude, *, datetime='current'):
        """Retrieve Nitrogen Dioxide index.

        ..Notes:
            cf. 'get_air_pollution_carbon_monoxyde' method

        :param float latitude: Latitude coordinate of location.
        :param float longitude: Longitude coordinate of location.
        :param str datetime: (optional, default 'current')
            ISO 8601 date (UTC time) or alias ('current').
        """
        extra_uri = '{},{}/{}.json'.format(latitude, longitude, datetime)
        return self._get_data(
            'air_pollution_nitrogen_dioxide', extra_uri=extra_uri)

    def get_uv_index_current(self, latitude, longitude):
        """Retrieve current UV (ultraviolet) index, by geographic coordinates.

        :param float latitude: Latitude coordinate of location.
        :param float longitude: Longitude coordinate of location.
        """
        # uv index API requires a specific order for query parameters...
        query_params = OrderedDict()
        query_params['lat'] = latitude
        query_params['lon'] = longitude
        return self._get_data(
            'uv_index_current', params=query_params, with_units=False)

    def get_uv_index_forecast(self, latitude, longitude):
        """Retrieve forecast UV (ultraviolet) index.

        :param float latitude: Latitude coordinate of location.
        :param float longitude: Longitude coordinate of location.
        """
        # uv index API requires a specific order for query parameters...
        query_params = OrderedDict()
        query_params['lat'] = latitude
        query_params['lon'] = longitude
        return self._get_data(
            'uv_index_forecast', params=query_params, with_units=False)

    def get_uv_index_historical(self, latitude, longitude, dt_start, dt_end):
        """Retrieve historical UV (ultraviolet) index.

        :param float latitude: Latitude coordinate of location.
        :param float longitude: Longitude coordinate of location.
        :param datetime dt_start: Starting point of time period.
        :param datetime dt_end: Final point of time period.
        """
        # uv index API requires a specific order for query parameters...
        query_params = OrderedDict()
        query_params['lat'] = latitude
        query_params['lon'] = longitude
        query_params['start'] = dt_start.timestamp()
        query_params['end'] = dt_end.timestamp()
        return self._get_data(
            'uv_index_historical', params=query_params, with_units=False)
