"""Some tools to make life easier."""

import datetime as dt


def dt_from_timestamp(timestamp, *, ts_tz=None):
    """Return a datetime converted from a timestamp value.

    :param float timestamp: Timestamp value to convert.
    :param datetime.timezone ts_tz: (optional, default None)
        Must the datetime result be timezone aware?
    :returns datetime: The converted timestamp in datetime object.
    """
    return dt.datetime.fromtimestamp(timestamp, tz=ts_tz)
