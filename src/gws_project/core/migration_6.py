from datetime import date, datetime

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.task.task_dto import TaskPriority, TaskStatus
from gws_project.task_history.task_history_event import TaskHistoryEvent
from gws_project.task_history.task_history_event_type import TaskHistoryEventType
from gws_project.task_history.task_history_value import (
    TaskHistoryTaskType,
    format_date_range,
)

# The English texts previous versions stored, mapped to the language-neutral value the app
# now translates. Statuses and priorities were written with `Enum.value.title()`.
_STATUS_VALUES = {status.value.title(): status.value for status in TaskStatus}
_PRIORITY_VALUES = {priority.value.title(): priority.value for priority in TaskPriority}
_TASK_TYPE_VALUES = {
    "a normal task": TaskHistoryTaskType.LEAF.value,
    "a task with subtasks": TaskHistoryTaskType.PARENT.value,
}

# How a date range used to be written, e.g. "Feb 01, 2025 → Feb 28, 2025", with "—" for a
# missing side.
_DATE_RANGE_SEPARATOR = " → "
_DATE_RANGE_PARTS = 2
_DATE_FORMAT = "%b %d, %Y"
_MISSING_DATE = "—"


def _convert_with(mapping: dict[str, str], value: str | None) -> str | None:
    """Map a stored English text to its neutral value, leaving anything unknown alone."""
    if not value:
        return value
    return mapping.get(value, value)


def _parse_old_date(text: str) -> date | None:
    """Read one side of an old date range: a date, or None when it was empty."""
    if text == _MISSING_DATE:
        return None
    return datetime.strptime(text, _DATE_FORMAT).date()


def _convert_date_range(value: str | None) -> str | None:
    """Re-encode "Feb 01, 2025 → Feb 28, 2025" as "2025-02-01|2025-02-28".

    Anything this cannot read is returned untouched: a history line that survives as
    English text is better than one that loses what it said.
    """
    if not value or _DATE_RANGE_SEPARATOR not in value:
        return value

    parts = [part.strip() for part in value.split(_DATE_RANGE_SEPARATOR)]
    if len(parts) != _DATE_RANGE_PARTS:
        return value

    try:
        start_date, end_date = (_parse_old_date(part) for part in parts)
    except ValueError:
        return value

    return format_date_range(start_date, end_date)


# The conversion each event type needs. Event types absent from this mapping stored free
# text (a title, a person's name, a project path): there is nothing to convert.
_CONVERTERS = {
    TaskHistoryEventType.STATUS_CHANGED: lambda value: _convert_with(_STATUS_VALUES, value),
    TaskHistoryEventType.PRIORITY_CHANGED: lambda value: _convert_with(_PRIORITY_VALUES, value),
    TaskHistoryEventType.TYPE_CHANGED: lambda value: _convert_with(_TASK_TYPE_VALUES, value),
    TaskHistoryEventType.DATES_CHANGED: _convert_date_range,
}


@brick_migration(
    "0.2.0-beta.10",
    short_description="Store task history values language-neutral so the app can translate them",
    db_manager=ProjectDbManager.get_instance(),
)
class Migration020Beta10(BrickMigration):
    """Convert the English texts stored in old history rows into neutral values.

    History rows used to store their old/new values already formatted in English ("Doing",
    "High", "a normal task", "Feb 01, 2025 → —"), and the sentence was built in English
    too. Both are now resolved in the reader's language from `event_type` and a neutral
    value, so the existing rows have to be converted - otherwise a French user would keep
    reading the English words of everything that happened before this version.
    """

    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        # The whole table is walked rather than filtered on `event_type`: a history table is
        # small, and this keeps the enum comparison in Python, where the mapping lives.
        for event in TaskHistoryEvent.select():
            convert = _CONVERTERS.get(event.event_type)
            if convert is None:
                continue

            old_value = convert(event.old_value)
            new_value = convert(event.new_value)

            if old_value == event.old_value and new_value == event.new_value:
                continue

            event.old_value = old_value
            event.new_value = new_value
            event.save()
