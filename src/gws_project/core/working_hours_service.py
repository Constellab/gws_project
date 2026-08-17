from gws_core import UnauthorizedException

from gws_project.core.working_hours_settings import WorkingHoursSettings
from gws_project.core.working_hours_settings_dto import WorkingHoursSettingsDTO
from gws_project.user.app_role_service import AppRoleService


class WorkingHoursService:
    """Service managing the single, app-wide working hours configuration."""

    @classmethod
    def get_settings(cls) -> WorkingHoursSettings:
        return WorkingHoursSettings.get_or_create_default()

    @classmethod
    def update_settings(
        cls, dto: WorkingHoursSettingsDTO, current_user_id: str
    ) -> WorkingHoursSettings:
        """Update the global working hours settings.

        Only users with the Admin app role may call this. This check is
        authoritative (does not trust the caller's own UI-level gating).
        """
        if not AppRoleService.is_admin(current_user_id):
            raise UnauthorizedException("Unauthorized: admin app role required")

        settings = cls.get_settings()
        settings.update_from_dto(dto)
        return settings.save()
