"""Initialization of OpenWeatherMap client API."""

__version__ = "0.1.0"


import logging


_LOGGER_NAME = __name__
# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(_LOGGER_NAME).addHandler(logging.NullHandler())


from .api_client import OpenWeatherMapClient  # flake8: noqa
