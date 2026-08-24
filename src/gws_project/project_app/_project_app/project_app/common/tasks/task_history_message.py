"""Builds the sentence of a task history event, in the language of the reader.

A history row stores what changed (`event_type`) and the values it changed between, kept
language-neutral on purpose (see the brick's `task_history_value`). The sentence is built
here, at display time, so the same row reads "a changé le statut de À faire à Terminé" or
"changed the status from To do to Done" depending on who is looking.

Both screens showing history go through this module - the task's Activity tab and the Home
feed - so their wording cannot drift apart. They differ only in how they name the task
(`HistorySubject`), since the feed already names it on a line of its own.
"""

from enum import Enum

from gws_project.task_history.task_history_event_type import TaskHistoryEventType
from gws_project.task_history.task_history_value import (
    DATE_RANGE_SEPARATOR,
    TaskHistoryTaskType,
    parse_date_range,
)
from gws_reflex_main import I18nState

from ..date_format import format_date
from . import task_history_translations  # noqa: F401  (side effect: registers translations)


class HistorySubject(Enum):
    """How a history sentence refers to the task the event happened on."""

    # The task's own Activity tab: the events are listed under the task.
    TIMELINE = "task_history.subject.timeline"
    # The Home feed: the task is named on a line of its own.
    FEED = "task_history.subject.feed"


# The template of each event type. ASSIGNEE_CHANGED is missing on purpose: its wording
# depends on whether the task was assigned, unassigned or reassigned.
_TEMPLATE_KEYS = {
    TaskHistoryEventType.CREATED: "task_history.created",
    TaskHistoryEventType.TITLE_CHANGED: "task_history.title_changed",
    TaskHistoryEventType.STATUS_CHANGED: "task_history.status_changed",
    TaskHistoryEventType.PRIORITY_CHANGED: "task_history.priority_changed",
    TaskHistoryEventType.DATES_CHANGED: "task_history.dates_changed",
    TaskHistoryEventType.DESCRIPTION_UPDATED: "task_history.description_updated",
    TaskHistoryEventType.MOVED: "task_history.moved",
    TaskHistoryEventType.TYPE_CHANGED: "task_history.type_changed",
}

# Event types whose values are a vocabulary of the app rather than free text, and the key
# prefix each one is translated with. Anything not listed here (a task title, a person's
# name, a project path) is shown as stored.
_VALUE_KEY_PREFIXES = {
    TaskHistoryEventType.STATUS_CHANGED: "task_history.status",
    TaskHistoryEventType.PRIORITY_CHANGED: "task_history.priority",
    TaskHistoryEventType.TYPE_CHANGED: "task_history.task_type",
}

# The English texts versions before 0.2.0-beta.10 stored for a TYPE_CHANGED event.
# Migration 6 rewrites them, but a lab that has not run it yet - or a row it could not
# convert - must still read in the user's language rather than show a raw value.
_LEGACY_TASK_TYPES = {
    "a normal task": TaskHistoryTaskType.LEAF.value,
    "a task with subtasks": TaskHistoryTaskType.PARENT.value,
}


def build_history_message(
    event_type: TaskHistoryEventType,
    old_value: str | None,
    new_value: str | None,
    is_automatic: bool,
    subject: HistorySubject,
    i18n: I18nState,
) -> str:
    """Build the sentence describing one history event.

    :param event_type: What the event recorded
    :type event_type: TaskHistoryEventType
    :param old_value: The value before the change, as stored
    :type old_value: str | None
    :param new_value: The value after the change, as stored
    :type new_value: str | None
    :param is_automatic: True when a parent task was recalculated from its subtasks
    :type is_automatic: bool
    :param subject: How the sentence should refer to the task
    :type subject: HistorySubject
    :param i18n: The i18n state holding the reader's language
    :type i18n: I18nState
    :return: The sentence, without the actor's name (the component renders it in front)
    :rtype: str
    """
    data = {
        "task": i18n.tr(subject.value),
        "old": _format_value(event_type, old_value, i18n),
        "new": _format_value(event_type, new_value, i18n),
    }

    if event_type == TaskHistoryEventType.ASSIGNEE_CHANGED:
        template_key = _assignee_template_key(old_value, new_value)
    else:
        # A new event type with no template of its own falls back to a generic line
        # rather than raising in the middle of a timeline.
        template_key = _TEMPLATE_KEYS.get(event_type, "task_history.changed")

    message = i18n.tr(template_key, data)

    if is_automatic:
        message += " " + i18n.tr("task_history.automatic_suffix")

    return message


def _assignee_template_key(old_value: str | None, new_value: str | None) -> str:
    """The template of an ASSIGNEE_CHANGED event: assigned, unassigned or reassigned."""
    if not old_value:
        return "task_history.assignee_set"
    if not new_value:
        return "task_history.assignee_unset"
    return "task_history.assignee_changed"


def _format_value(
    event_type: TaskHistoryEventType, value: str | None, i18n: I18nState
) -> str:
    """Turn one stored value into the text the reader sees.

    A status, a priority and a task type are vocabularies of the app, so they are
    translated; a date range is decoded and formatted in the reader's language; everything
    else is free text written by a user and shown as it is.
    """
    if value is None:
        return ""

    if event_type == TaskHistoryEventType.DATES_CHANGED:
        return _format_date_range(value, i18n)

    prefix = _VALUE_KEY_PREFIXES.get(event_type)
    if not prefix:
        return value

    normalized = _normalize_vocabulary_value(event_type, value)

    # Falls back to the stored value: a user must never be shown a translation key,
    # even for a value no version of the app ever wrote ("task_history.status.Doing"
    # instead of "Doing" is a bug, not a translation).
    return _translate_or(i18n, f"{prefix}.{normalized}", value)


def _normalize_vocabulary_value(event_type: TaskHistoryEventType, value: str) -> str:
    """Turn a stored vocabulary value into the key suffix it is registered under.

    Accepts both encodings: the neutral value written since 0.2.0-beta.10 ("DOING") and
    the English label written before it ("Doing", "a normal task").
    """
    if event_type == TaskHistoryEventType.TYPE_CHANGED:
        normalized = value.strip()
        return _LEGACY_TASK_TYPES.get(normalized.lower(), normalized)

    # Statuses and priorities used to be stored title-cased; their neutral value is the
    # enum's, upper-case.
    return value.strip().upper()


def _translate_or(i18n: I18nState, key: str, fallback: str) -> str:
    """Translate `key`, or return `fallback` when it is not registered.

    A missing key resolves to the key itself (see gws_reflex_base's `resolve`), which is
    the one thing a user must never read. Every key built from data - as opposed to
    written in the code - goes through here.
    """
    translated = i18n.tr(key)
    return fallback if translated == key else translated


def _format_date_range(value: str, i18n: I18nState) -> str:
    """Format a stored date range, e.g. "Feb 1, 2025 → Feb 28, 2025".

    A value written before 0.2.0-beta.10 is already a formatted range rather than the
    encoded one; it is shown as it is (in English, but true) instead of being read as
    two missing dates.
    """
    if DATE_RANGE_SEPARATOR not in value:
        return value

    start_date, end_date = parse_date_range(value)
    no_date = i18n.tr("task_history.no_date")

    start_text = format_date(start_date, i18n.lang) or no_date
    end_text = format_date(end_date, i18n.lang) or no_date

    return f"{start_text} → {end_text}"
