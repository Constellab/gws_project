from gws_core import TypedCharField, TypedFloatField, TypedJSONField

from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.core.working_hours_settings_dto import WorkingHoursSettingsDTO


def _default_working_days() -> list[int]:
    return [0, 1, 2, 3, 4]  # Monday to Friday


class WorkingHoursSettings(ModelWithUser):
    """Single, app-wide working hours configuration.

    There is only ever one row in this table (see get_or_create_default);
    it is not scoped per user.
    """

    working_days = TypedJSONField(default=_default_working_days)  # list[int], 0=Mon..6=Sun
    weekly_hours = TypedFloatField(default=35.0)  # total hours worked per week, e.g. 35
    timezone = TypedCharField(default="Europe/Paris")
    day_start_time = TypedCharField(default="09:00")  # "HH:MM"
    day_end_time = TypedCharField(default="18:00")  # "HH:MM"
    lunch_start_time = TypedCharField(default="12:00")  # "HH:MM"
    lunch_end_time = TypedCharField(default="13:00")  # "HH:MM"

    def to_dto(self) -> WorkingHoursSettingsDTO:
        return WorkingHoursSettingsDTO(
            working_days=self.working_days,
            weekly_hours=self.weekly_hours,
            timezone=self.timezone,
            day_start_time=self.day_start_time,
            day_end_time=self.day_end_time,
            lunch_start_time=self.lunch_start_time,
            lunch_end_time=self.lunch_end_time,
        )

    def update_from_dto(self, dto: WorkingHoursSettingsDTO) -> None:
        self.working_days = dto.working_days
        self.weekly_hours = dto.weekly_hours
        self.timezone = dto.timezone
        self.day_start_time = dto.day_start_time
        self.day_end_time = dto.day_end_time
        self.lunch_start_time = dto.lunch_start_time
        self.lunch_end_time = dto.lunch_end_time

    @classmethod
    def get_or_create_default(cls) -> "WorkingHoursSettings":
        """Return the single global settings row, creating it with defaults if missing."""
        settings = cls.select().first()
        if settings is None:
            settings = cls()
            settings.save()
        return settings

    class Meta:
        table_name = "gws_project_working_hours_settings"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
