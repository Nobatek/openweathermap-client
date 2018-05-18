"""Tests for OpenWeatherMapClient."""

import datetime as dt

import pytest
from tests.utils import isclose

from requests.exceptions import HTTPError as req_HTTPError

from openweathermap_client import OpenWeatherMapClient
from openweathermap_client.exceptions import OWMClientKeyNotDefinedError
from openweathermap_client.api_client import (
    _API_HOST, _DEFAULT_MAX_RETRIES, _DEFAULT_UNITS)


class TestOpenWeatherMapClient():
    """OpenWeatherMap api client tests."""

    def test_openweathermap_client(self, apikey, apihost):
        """Test api client init."""

        client = OpenWeatherMapClient(apikey, host=apihost)
        assert client.api_key == apikey
        assert client.host == apihost
        assert client.max_retries == _DEFAULT_MAX_RETRIES
        assert client._base_uri == 'https://{}'.format(apihost)
        assert client._base_uri_params == {
            'appid': apikey, 'units': _DEFAULT_UNITS}
        assert client.last_uri_call is None

        client = OpenWeatherMapClient(
            apikey, use_ssl=False, max_retries=3, units='standard')
        assert client.api_key == apikey
        assert client.host == _API_HOST
        assert client.max_retries == 3
        assert client._base_uri == 'http://{}'.format(_API_HOST)
        assert client._base_uri_params == {
            'appid': apikey, 'units': 'standard'}
        assert client.last_uri_call is None

        client = OpenWeatherMapClient(apikey, max_retries=-1)
        assert client.max_retries == _DEFAULT_MAX_RETRIES

    @pytest.mark.slow
    def test_openweathermap_client_city_list(self, apikey, apihost):
        """Test api client get city list."""

        # get api client
        client = OpenWeatherMapClient(apikey, host=apihost)

        # get cities list
        result_data = client.get_city_list()
        assert len(result_data) > 0
        assert result_data[0]['id'] is not None
        assert result_data[0]['name'] is not None
        assert result_data[0]['coord'] is not None
        assert result_data[0]['coord']['latitude'] is not None
        assert result_data[0]['coord']['longitude'] is not None

    def test_openweathermap_client_city_list_faster(self, apikey, apihost):
        """Test api client get city list (faster mode)."""

        # get api client
        client = OpenWeatherMapClient(apikey, host=apihost)

        # get cities list
        # not validating data with marshmallow is faster
        result_data = client.get_city_list(validate_with_schema=False)
        assert len(result_data) > 0
        assert result_data[0]['id'] is not None
        assert result_data[0]['name'] is not None
        assert result_data[0]['coord'] is not None
        # note that result is not quite the same as in test case above...
        assert result_data[0]['coord']['lat'] is not None
        assert result_data[0]['coord']['lon'] is not None

    def test_openweathermap_client_forecast(self, apikey, apihost, city_info):
        """Test api client get forecast data."""

        def _assert_data(result_data, check_city=True):
            # city data
            if check_city:
                assert result_data['city']['id'] == city_info['_id']
                assert result_data['city']['name'] == city_info['name']
                assert result_data['city']['country'] == city_info['country']
                assert isclose(
                    result_data['city']['coord']['latitude'],
                    city_info['coord']['lat'], rel_tol=1e-02)
                assert isclose(
                    result_data['city']['coord']['longitude'],
                    city_info['coord']['lon'], rel_tol=1e-02)

            # forecast data
            datas = result_data['datas']
            assert datas is not None
            assert result_data['cnt'] == len(datas)
            assert len(datas) > 0
            assert isinstance(datas[0]['dt_value'], dt.datetime)
            assert datas[0]['main']['temp'] is not None
            assert datas[0]['main']['temp_min'] is not None
            assert datas[0]['main']['temp_max'] is not None
            assert datas[0]['main']['humidity'] is not None
            assert datas[0]['main']['pressure'] is not None
            assert datas[0]['main']['sea_level'] is not None
            assert datas[0]['main']['grnd_level'] is not None

        # get api client
        client = OpenWeatherMapClient(apikey)

        # get forecast data by city id
        result_data = client.get_forecast_by_city_id(city_info['_id'])
        _assert_data(result_data)

        # get forecast data by geographic coordinates
        result_data = client.get_forecast_by_coord(
            city_info['coord']['lat'], city_info['coord']['lon'])
        _assert_data(result_data)

        # get forecast data by city name
        result_data = client.get_forecast_by_city_name(
            city_info['name'], country_code=city_info['country'])
        _assert_data(result_data, check_city=False)

        # get forecast data by zip code
        result_data = client.get_forecast_by_zip_code(
            city_info['zip_code'], city_info['country'])
        _assert_data(result_data, check_city=False)

    def test_openweathermap_client_current_weather(self, apikey, city_info):
        """Test api client get current weather."""

        def _assert_data(result_data, check_city=True):
            # city data
            if check_city:
                assert result_data['city_id'] == city_info['_id']
                assert result_data['city_name'] == city_info['name']
                assert result_data['sys']['country'] == city_info['country']
                assert isclose(
                    result_data['city_coord']['latitude'],
                    city_info['coord']['lat'], rel_tol=1e-02)
                assert isclose(
                    result_data['city_coord']['longitude'],
                    city_info['coord']['lon'], rel_tol=1e-02)

            # current weather data
            assert isinstance(result_data['dt_value'], dt.datetime)
            assert result_data['main']['temp'] is not None
            assert result_data['main']['temp_min'] is not None
            assert result_data['main']['temp_max'] is not None
            assert result_data['main']['humidity'] is not None
            assert result_data['main']['pressure'] is not None

        # get api client
        client = OpenWeatherMapClient(apikey)

        # get current weather data by city id
        result_data = client.get_current_weather_by_city_id(city_info['_id'])
        _assert_data(result_data)

        # get current weather data by geographic coordinates
        result_data = client.get_current_weather_by_coord(
            city_info['coord']['lat'], city_info['coord']['lon'])
        _assert_data(result_data)

        # get current weather data by city name
        result_data = client.get_current_weather_by_city_name(
            city_info['name'], country_code=city_info['country'])
        _assert_data(result_data, check_city=False)

        # get current weather data by zip code
        result_data = client.get_current_weather_by_zip_code(
            city_info['zip_code'], city_info['country'])
        _assert_data(result_data, check_city=False)

    def test_openweathermap_client_current_weather_extra(
            self, apikey, city_info, city_ids):
        """Test api client get current weather extra functions."""

        # get api client
        client = OpenWeatherMapClient(apikey)

        # get current weather data for a list of city IDs
        result_data = client.get_current_weather_group(city_ids)
        assert len(result_data['datas']) == 2

        # get current weather data by geographic coordinates: within box
        result_data = client.get_current_weather_within_box(
            [12, 32, 15, 37], 10)
        assert len(result_data['datas']) == 15

        # get current weather data by geographic coordinates: within circle
        result_data = client.get_current_weather_within_circle(
            city_info['coord']['lat'], city_info['coord']['lon'])
        assert len(result_data['datas']) == 10

    def test_openweathermap_client_air_pollution(self, apikey, apihost):
        """Test api client get air pollution data."""

        # get api client
        client = OpenWeatherMapClient(apikey, host=apihost, use_ssl=False)

        # get air pollution carbon monoxyde
        result_data = client.get_air_pollution_carbon_monoxyde(
            0.0, 10.0, datetime='2016-12-25Z')
        assert result_data is not None
        assert len(result_data['datas']) > 0

        # get air pollution ozone
        result_data = client.get_air_pollution_ozone(0.0, 10.0)
        assert result_data is not None

        # get air pollution sulfur dioxide
        result_data = client.get_air_pollution_sulfur_dioxide(
            0.0, 10.0, datetime='2016-12-25Z')
        assert result_data is not None
        assert len(result_data['datas']) > 0

        # get air pollution nitrogen dioxide
        result_data = client.get_air_pollution_nitrogen_dioxide(
            0.0, 10.0, datetime='2016-12Z')
        assert result_data is not None

    def test_openweathermap_client_uv_index(self, apikey, apihost):
        """Test api client get uv index data."""

        # get api client
        client = OpenWeatherMapClient(apikey, host=apihost, use_ssl=False)

        # get current uv index
        result_data = client.get_uv_index_current(37.75, -122.37)
        assert result_data is not None
        assert result_data['latitude'] == 37.75
        assert result_data['longitude'] == -122.37
        assert result_data['value'] is not None

        # get forecast uv index
        result_datas = client.get_uv_index_forecast(37.75, -122.37)
        assert result_datas is not None
        assert len(result_data) > 0
        assert result_datas[0]['latitude'] == 37.75
        assert result_datas[0]['longitude'] == -122.37
        assert result_datas[0]['value'] is not None

        # get historical uv index
        dt_start = dt.datetime(2017, 6, 21, 12, 59, 13, tzinfo=dt.timezone.utc)
        dt_end = dt.datetime(2017, 6, 26, 12, 59, 51, tzinfo=dt.timezone.utc)
        result_datas = client.get_uv_index_historical(
            37.75, -122.37, dt_start=dt_start, dt_end=dt_end)
        assert result_datas is not None
        assert len(result_datas) > 0
        assert result_datas[0]['latitude'] == 37.75
        assert result_datas[0]['longitude'] == -122.37
        assert result_datas[0]['value'] is not None

    def test_openweathermap_client_errors(self, city_info):
        """Test errors on api client."""

        # api_key is None
        with pytest.raises(OWMClientKeyNotDefinedError):
            OpenWeatherMapClient(None)

        # api_key is wrong: 401
        client = OpenWeatherMapClient('wrong')
        with pytest.raises(req_HTTPError):
            client.get_forecast_by_city_id(city_info['_id'])
