"""How a TaskHistoryEvent encodes the values it stores.

A history row is immutable and read back long after it was written, by users who may not
read the same language. Its `old_value`/`new_value` are therefore stored
**language-neutral** - an enum value, an ISO date range - and the sentence shown to a user
is built at display time, in their language, by the app layer
(`common/tasks/task_history_message.py`).

Free-text values (a task title, a person's name, a project/task path) are stored as they
are: there is nothing to translate in them.

This module owns that encoding: the service writes through it, the app reads through it.
"""

from datetime import date
from enum import Enum

# Separates the two dates of a DATES_CHANGED value. Deliberately not the "→" the user
# eventually sees: this is a storage format, and the arrow is part of the display.
DATE_RANGE_SEPARATOR = "|"

# A date range always has both of its sides, even when one of them is empty.
_DATE_RANGE_PARTS = 2


class TaskHistoryTaskType(Enum):
    """The two values a TYPE_CHANGED event stores: what the task was, and what it became."""

    # A task managing its own status/priority/dates.
    LEAF = "LEAF"
    # A task whose status/priority/dates are computed from its subtasks.
    PARENT = "PARENT"


def format_date_range(start_date: date | None, end_date: date | None) -> str:
    """Encode a start/end date pair for storage in a DATES_CHANGED event.

    An absent date is encoded as an empty side, so a range keeps its two halves and the
    reader can tell which one is missing.

    :param start_date: The start date, if any
    :type start_date: date | None
    :param end_date: The end date, if any
    :type end_date: date | None
    :return: The encoded range, e.g. "2025-02-01|2025-02-28"
    :rtype: str
    """
    start_text = start_date.isoformat() if start_date else ""
    end_text = end_date.isoformat() if end_date else ""

    return f"{start_text}{DATE_RANGE_SEPARATOR}{end_text}"


def parse_date_range(value: str | None) -> tuple[date | None, date | None]:
    """Decode a DATES_CHANGED value back into its two dates.

    Tolerates anything that is not a well-formed range (an empty side, a value written by
    an older version of the brick) by returning None for the side it cannot read: a
    history line must stay readable, never raise.

    :param value: The stored value
    :type value: str | None
    :return: The start and end dates, either of which may be None
    :rtype: tuple[date | None, date | None]
    """
    if not value:
        return None, None

    parts = value.split(DATE_RANGE_SEPARATOR)
    if len(parts) != _DATE_RANGE_PARTS:
        return None, None

    return _parse_date(parts[0]), _parse_date(parts[1])


def _parse_date(value: str) -> date | None:
    """Read one ISO date, or None when it is absent or unreadable."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
