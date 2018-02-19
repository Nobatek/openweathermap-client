"""Fixtures for OpenWeatherMapClient tests."""

import pytest


@pytest.fixture
def apihost(request):
    """Return an api_host for OpenWeatherMap API."""
    # samples api host
    return 'samples.openweathermap.org'


@pytest.fixture
def apikey(request):
    """Return an api_key for OpenWeatherMap API."""
    # available free api keys :
    #  ae0c16c7a7c591f9d88e50954c9b2c0b, b6907d289e10d714a6e88b30761fae22,
    #  b1b15e88fa797225412429c1c50c122a1, ...
    return 'ae0c16c7a7c591f9d88e50954c9b2c0b'


@pytest.fixture
def city_info(request):
    """Return an OpenWeatherMap API city location."""
    return {
        '_id': 6434841,
        'name': 'Montcuq',
        'country': 'FR',
        'zip_code': 46800,
        'coord': {
            'lon': 1.21667,
            'lat': 44.333328
        }
    }


@pytest.fixture
def city_ids(request):
    """Return a list of OpenWeatherMap API city ID."""
    return (6434841, 2992790,)
