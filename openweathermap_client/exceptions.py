"""OpenWeatherMap API client exceptions."""

from marshmallow import ValidationError


class OpenWeatherMapClientError(Exception):
    """Generic OpenWeatherMap API client exception."""


class OWMClientKeyNotDefinedError(OpenWeatherMapClientError):
    """OpenWeatherMap API key not defined error."""


class OWMClientUnknownServiceNameError(OpenWeatherMapClientError):
    """OpenWeatherMap API service unknown error."""


class OWMClientAccessLimitationError(OpenWeatherMapClientError):
    """OpenWeatherMap API service access limitation error."""


class OWMClientValidationError(OpenWeatherMapClientError, ValidationError):
    """OpenWeatherMap API data validation error."""
