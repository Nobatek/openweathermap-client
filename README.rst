=====================
openweathermap-client
=====================

.. image:: https://img.shields.io/travis/Nobatek/openweathermap-client/master.svg
        :target: https://travis-ci.org/Nobatek/openweathermap-client
        :alt: Build status

.. image:: https://coveralls.io/repos/github/Nobatek/openweathermap-client/badge.svg?branch=master
        :target: https://coveralls.io/github/Nobatek/openweathermap-client/?branch=master
        :alt: Code coverage

About
=====

`OpenWeatherMap API <https://openweathermap.org/api>`_ client to retrieve
current weather and forecasts for cities over the world, and concentrating on
free access datas.

Examples
========

.. code-block:: python

    from openweathermap_client import OpenWeatherMapClient
    from openweathermap_client.exceptions import OWMClientAccessLimitationError

    # Init client with your personal API key
    client = OpenWeatherMapClient('api_key_here')

    try:
        # Get forecast data by city ID
        result_data = client.get_forecast_by_city_id('city_id')
        # Response contains information about 5 day / 3 hour forecast,
        #  see https://openweathermap.org/forecast5#parameter
    except OWMClientAccessLimitationError as exc:
        # Remember to catch exceptions when sending requests...
        pass

Installation
============

.. code-block:: shell

    pip install setup.py

Development
===========

**Use a virtual environnement to debug or develop**

.. code-block:: shell

    # Create virtual environment
    $ virtualenv -p /usr/bin/python3 $VIRTUALENVS_DIR/openweathermap-client

    # Activate virtualenv
    $ source $VIRTUALENVS_DIR/openweathermap-client/bin/activate

**Tests**

.. code-block:: shell

    # Install test dependencies
    $ pip install -e .[test]

    # Run tests
    $ py.test

    # Skip slow tests
    $ py.test -m 'not slow'

    # Run tests with coverage
    $ py.test --cov=openweathermap_client --cov-report term-missing
