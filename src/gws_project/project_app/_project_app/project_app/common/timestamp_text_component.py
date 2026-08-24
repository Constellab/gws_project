from datetime import datetime

from .date_format import format_datetime


def format_timestamp(value: datetime | None, lang: str) -> str:
    """Format a datetime value (e.g. created_at, last_modified_at) as a localized
    string including the time of day.

    Formatting happens server-side on the real Python ``datetime`` value, and the
    result is sent to the frontend as a plain string. This avoids depending on the
    browser/moment.js to parse a serialized datetime string, which proved unreliable:
    the backend serializes datetimes with a space separator and a variable
    fractional-second length (e.g. "2026-07-24 13:59:20+00:00", or
    "...20.123456+00:00" for a just-created record still holding microseconds before
    its next DB round-trip), a shape that some client-side date parsers mishandle.

    :param value: The datetime value to format
    :type value: datetime | None
    :param lang: The active language code (``I18nState.lang``), used for the month name
    :type lang: str
    :return: The formatted timestamp string, or "" if value is None
    :rtype: str
    """
    return format_datetime(value, lang)
