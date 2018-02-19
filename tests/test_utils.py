"""Tests for OpenWeatherMap utils."""

import datetime as dt

from openweathermap_client.utils import dt_from_timestamp


class TestUtils():
    """Utils tests."""

    def test_utils_dt_from_timestamp(self):
        """Tests from timestamp conversion."""

        # with timezone awareness
        dt_utcnow = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
        ts_utcnow = dt_utcnow.timestamp()
        assert dt_from_timestamp(ts_utcnow, ts_tz=dt.timezone.utc) == dt_utcnow
        assert dt_from_timestamp(ts_utcnow) != dt_utcnow

        # without timezone awareness
        dt_now = dt.datetime.now()
        ts_now = dt_now.timestamp()
        assert dt_from_timestamp(ts_now, ts_tz=dt.timezone.utc) != dt_now
        assert dt_from_timestamp(ts_now) == dt_now
