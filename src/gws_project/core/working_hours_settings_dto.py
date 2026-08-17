from gws_core import BaseModelDTO


class WorkingHoursSettingsDTO(BaseModelDTO):
    """DTO for the app-wide working hours configuration."""

    working_days: list[int]  # 0=Mon..6=Sun
    weekly_hours: float  # total hours worked per week, e.g. 35
    timezone: str
    day_start_time: str  # "HH:MM"
    day_end_time: str  # "HH:MM"
    lunch_start_time: str  # "HH:MM"
    lunch_end_time: str  # "HH:MM"
