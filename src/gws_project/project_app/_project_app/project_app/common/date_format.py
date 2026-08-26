"""Language-aware formatting of the dates the user reads.

Dates and datetimes are stored language-neutrally: a real date/datetime column in the
database, and - for the `*_text` fields a model DTO carries - an ISO fallback. Everything
a user *reads* goes through this module, which renders day, month and weekday names in
the language selected in the app (`I18nState.lang`) instead of Python's English
`strftime` output.

The month/weekday names are explicit tables rather than a C locale: a single Reflex
process serves every session, so switching the process locale per request is not an
option, and the app only offers the two languages of `SUPPORTED_LANGS`.

Formatting happens server-side, on the real Python date, and reaches the frontend as a
plain string (see `timestamp_text_component.format_timestamp` for why client-side
parsing was ruled out). A state therefore formats with the language of the session at
load time; the language toggle lives on the Settings page, so any other page is (re)loaded
after a language change and picks the new language up.
"""

from datetime import date, datetime

from gws_project.project.project_dto import ProjectDTO
from gws_project.task.task_dto import TaskDTO
from gws_project.template.project_template_dto import ProjectTemplateDTO

# Language used when a language code has no table of its own (the app's default language,
# see LanguageInitState).
FALLBACK_LANG = "en"

_MONTHS_SHORT: dict[str, list[str]] = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin",
           "juil.", "août", "sept.", "oct.", "nov.", "déc."],
}

_MONTHS_LONG: dict[str, list[str]] = {
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin",
           "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
}

# Weekday tables are indexed by `date.weekday()` (0 = Monday).
_WEEKDAYS_SHORT: dict[str, list[str]] = {
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "fr": ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."],
}

_WEEKDAYS_LONG: dict[str, list[str]] = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
}

# Ordering patterns, keyed by format name then language. Placeholders are the token names
# built by `_tokens`. A new language needs one entry per pattern plus the name tables
# above; a missing one falls back to FALLBACK_LANG rather than crashing.
_PATTERNS: dict[str, dict[str, str]] = {
    # "Aug 21, 2026" / "21 août 2026"
    "date": {"en": "{month_short} {day}, {year}", "fr": "{day} {month_short} {year}"},
    # "Aug 21" / "21 août"
    "day_month": {"en": "{month_short} {day}", "fr": "{day} {month_short}"},
    # "Thursday 21 August" / "jeudi 21 août"
    "weekday_date": {
        "en": "{weekday_long} {day} {month_long}",
        "fr": "{weekday_long} {day} {month_long}",
    },
    # "Thursday 21 August 2026" / "jeudi 21 août 2026"
    "weekday_date_year": {
        "en": "{weekday_long} {day} {month_long} {year}",
        "fr": "{weekday_long} {day} {month_long} {year}",
    },
    # "Thu 21" / "jeu. 21"
    "short_weekday_day": {"en": "{weekday_short} {day}", "fr": "{weekday_short} {day}"},
    # "Thu Aug 21" / "jeu. 21 août"
    "short_weekday_day_month": {
        "en": "{weekday_short} {month_short} {day}",
        "fr": "{weekday_short} {day} {month_short}",
    },
}


def _table(table: dict[str, list[str]], lang: str) -> list[str]:
    """Return a name table for a language, falling back to FALLBACK_LANG."""
    return table.get(lang) or table[FALLBACK_LANG]


def _tokens(value: date, lang: str) -> dict[str, object]:
    """Build the placeholder values available to the patterns for one date."""
    return {
        "day": value.day,
        "year": value.year,
        "month_short": _table(_MONTHS_SHORT, lang)[value.month - 1],
        "month_long": _table(_MONTHS_LONG, lang)[value.month - 1],
        "weekday_short": _table(_WEEKDAYS_SHORT, lang)[value.weekday()],
        "weekday_long": _table(_WEEKDAYS_LONG, lang)[value.weekday()],
    }


def _render(pattern_name: str, value: date | None, lang: str) -> str:
    """Render a date with one of the `_PATTERNS`, or "" when there is no date."""
    if value is None:
        return ""

    patterns = _PATTERNS[pattern_name]
    pattern = patterns.get(lang) or patterns[FALLBACK_LANG]

    return pattern.format(**_tokens(value, lang))


def format_date(value: date | None, lang: str) -> str:
    """Format a date with a short month name: "Aug 21, 2026" / "21 août 2026".

    :param value: The date (or datetime) to format
    :type value: date | None
    :param lang: The active language code
    :type lang: str
    :return: The formatted date, or "" if value is None
    :rtype: str
    """
    return _render("date", value, lang)


def format_day_month(value: date | None, lang: str) -> str:
    """Format a date without its year: "Aug 21" / "21 août".

    Used where the year is already obvious from the context (a due date within the
    current planning week, for instance).

    :param value: The date to format
    :type value: date | None
    :param lang: The active language code
    :type lang: str
    :return: The formatted date, or "" if value is None
    :rtype: str
    """
    return _render("day_month", value, lang)


def format_time(value: datetime | None) -> str:
    """Format the time of day of a datetime: "14:32".

    Language-neutral (24-hour clock), kept here so callers have a single import.

    :param value: The datetime to read the time from
    :type value: datetime | None
    :return: The formatted time, or "" if value is None
    :rtype: str
    """
    if value is None:
        return ""
    return value.strftime("%H:%M")


def format_datetime(value: datetime | None, lang: str) -> str:
    """Format a datetime as a date followed by its time: "Aug 21, 2026 14:32".

    :param value: The datetime to format
    :type value: datetime | None
    :param lang: The active language code
    :type lang: str
    :return: The formatted datetime, or "" if value is None
    :rtype: str
    """
    if value is None:
        return ""
    return f"{format_date(value, lang)} {format_time(value)}"


def format_weekday_date(value: date | None, lang: str, with_year: bool = False) -> str:
    """Format a date with its weekday and full month name.

    "Thursday 21 August" / "jeudi 21 août", plus the year when `with_year` is set. Used
    for the day headings of the Home and My work screens.

    :param value: The date to format
    :type value: date | None
    :param lang: The active language code
    :type lang: str
    :param with_year: Whether to append the year
    :type with_year: bool
    :return: The formatted date, or "" if value is None
    :rtype: str
    """
    return _render("weekday_date_year" if with_year else "weekday_date", value, lang)


def format_short_weekday_day(value: date | None, lang: str) -> str:
    """Format a date as a short weekday and day number: "Thu 21" / "jeu. 21".

    Used for the column headers of the Planning grid.

    :param value: The date to format
    :type value: date | None
    :param lang: The active language code
    :type lang: str
    :return: The formatted date, or "" if value is None
    :rtype: str
    """
    return _render("short_weekday_day", value, lang)


def format_short_weekday_day_month(value: date | None, lang: str) -> str:
    """Format a date as a short weekday, day and short month: "Thu Aug 21" / "jeu. 21 août".

    :param value: The date to format
    :type value: date | None
    :param lang: The active language code
    :type lang: str
    :return: The formatted date, or "" if value is None
    :rtype: str
    """
    return _render("short_weekday_day_month", value, lang)


def format_short_weekday_time(value: datetime | None, lang: str) -> str:
    """Format a datetime as a short weekday and time: "Thu 14:00" / "jeu. 14:00".

    Used by the "scheduled <when>" badge of the My work screen.

    :param value: The datetime to format
    :type value: datetime | None
    :param lang: The active language code
    :type lang: str
    :return: The formatted datetime, or "" if value is None
    :rtype: str
    """
    if value is None:
        return ""
    return f"{_table(_WEEKDAYS_SHORT, lang)[value.weekday()]} {format_time(value)}"


def format_date_range(start: date | None, end: date | None, lang: str) -> str:
    """Format a date range, keeping the year only on its end: "Aug 17 - Aug 23, 2026".

    :param start: The first day of the range
    :type start: date | None
    :param end: The last day of the range
    :type end: date | None
    :param lang: The active language code
    :type lang: str
    :return: The formatted range
    :rtype: str
    """
    return f"{format_day_month(start, lang)} - {format_date(end, lang)}"


def localize_task_dto(dto: TaskDTO, lang: str) -> TaskDTO:
    """Fill a TaskDTO's date texts in the active language.

    `Task.to_dto()` cannot know the language of the session, so it leaves ISO fallbacks
    in `start_date_text`/`due_date_text`. Every state that sends tasks to the frontend
    passes them through here (mutates and returns the DTO, so it can be used inline in a
    comprehension).

    :param dto: The task DTO to localize
    :type dto: TaskDTO
    :param lang: The active language code
    :type lang: str
    :return: The same DTO, with localized date texts
    :rtype: TaskDTO
    """
    dto.start_date_text = format_date(dto.start_date, lang)
    dto.due_date_text = format_date(dto.due_date, lang)
    return dto


def localize_project_template_dto(
    dto: ProjectTemplateDTO, lang: str
) -> ProjectTemplateDTO:
    """Fill a ProjectTemplateDTO's creation timestamp in the active language.

    See `localize_task_dto`.

    :param dto: The project template DTO to localize
    :type dto: ProjectTemplateDTO
    :param lang: The active language code
    :type lang: str
    :return: The same DTO, with a localized creation timestamp
    :rtype: ProjectTemplateDTO
    """
    dto.created_at_text = format_datetime(dto.created_at, lang)
    return dto


def localize_project_dto(dto: ProjectDTO, lang: str) -> ProjectDTO:
    """Fill a ProjectDTO's date texts in the active language.

    See `localize_task_dto`.

    :param dto: The project DTO to localize
    :type dto: ProjectDTO
    :param lang: The active language code
    :type lang: str
    :return: The same DTO, with localized date texts
    :rtype: ProjectDTO
    """
    dto.start_date_text = format_date(dto.start_date, lang)
    dto.due_date_text = format_date(dto.due_date, lang)
    return dto
