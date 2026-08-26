import reflex as rx
from gws_project.core.working_hours_service import WorkingHoursService
from gws_project.core.working_hours_settings_dto import WorkingHoursSettingsDTO
from gws_project.user.app_role_service import AppRoleService
from gws_project.user.user import User
from gws_project.user.user_app_role import AppRole
from gws_reflex_main import ReflexMainState, toast_tr

from .settings_dto import UserRowDTO


class SettingsState(rx.State):
    """State for the Settings page: language (I18nState is used directly by the
    component), roles (list + change, open to everyone), and the app-wide
    working hours settings (admin-only)."""

    is_admin: bool = False

    users: list[UserRowDTO] = []

    working_days: list[int] = []
    weekly_hours: str = ""
    timezone: str = ""
    day_start_time: str = ""
    day_end_time: str = ""
    lunch_start_time: str = ""
    lunch_end_time: str = ""

    async def on_load(self):
        """Load the roles list for everyone, and working hours for admins only."""
        main_state = await self.get_state(ReflexMainState)
        if not await main_state.check_authentication():
            return

        current_user = await main_state.get_and_check_current_user()
        self.is_admin = AppRoleService.is_admin(current_user.id)

        await self._load_users(main_state)

        if self.is_admin:
            self._load_working_hours()

    async def _load_users(self, main_state: ReflexMainState):
        with await main_state.authenticate_user():
            users = User.get_real_users()
            self.users = [
                UserRowDTO(user=user.to_dto(), role=AppRoleService.get_role_for_user(user.id))
                for user in users
            ]

    @rx.event
    async def change_user_role(self, user_id: str, new_role: str):
        """Change the app role of any user. Deliberately open to everyone."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            AppRoleService.set_role_for_user(user_id, AppRole[new_role])

        await self._load_users(main_state)

        # Re-check the current session user's own admin status immediately,
        # in case they just changed their own role: the Working Hours section
        # must appear/disappear right away, without navigating away and back.
        current_user = await main_state.get_and_check_current_user()
        self.is_admin = AppRoleService.is_admin(current_user.id)
        if self.is_admin:
            self._load_working_hours()

        yield await toast_tr.success(self, "settings.roles.updated")

    def _load_working_hours(self):
        settings = WorkingHoursService.get_settings()
        self.working_days = settings.working_days
        self.weekly_hours = f"{settings.weekly_hours:g}"
        self.timezone = settings.timezone
        self.day_start_time = settings.day_start_time
        self.day_end_time = settings.day_end_time
        self.lunch_start_time = settings.lunch_start_time
        self.lunch_end_time = settings.lunch_end_time

    @rx.event
    def toggle_working_day(self, day: int, checked: bool):
        """Toggle a single weekday (0=Mon..6=Sun) in the working days list."""
        if checked and day not in self.working_days:
            self.working_days = [*self.working_days, day]
        elif not checked and day in self.working_days:
            self.working_days = [d for d in self.working_days if d != day]

    @rx.event
    def set_weekly_hours(self, value: str):
        self.weekly_hours = value

    @rx.event
    def set_timezone(self, value: str):
        self.timezone = value

    @rx.event
    def set_day_start_time(self, value: str):
        self.day_start_time = value

    @rx.event
    def set_day_end_time(self, value: str):
        self.day_end_time = value

    @rx.event
    def set_lunch_start_time(self, value: str):
        self.lunch_start_time = value

    @rx.event
    def set_lunch_end_time(self, value: str):
        self.lunch_end_time = value

    @rx.event
    async def save_working_hours(self):
        """Save the app-wide working hours settings. Admin-only."""
        if not self.is_admin:
            yield await toast_tr.error(self, "settings.working_hours.unauthorized")
            return

        try:
            weekly_hours = float(self.weekly_hours)
        except ValueError:
            yield await toast_tr.error(self, "settings.working_hours.invalid_weekly_hours")
            return

        main_state = await self.get_state(ReflexMainState)
        current_user = await main_state.get_and_check_current_user()

        dto = WorkingHoursSettingsDTO(
            working_days=self.working_days,
            weekly_hours=weekly_hours,
            timezone=self.timezone,
            day_start_time=self.day_start_time,
            day_end_time=self.day_end_time,
            lunch_start_time=self.lunch_start_time,
            lunch_end_time=self.lunch_end_time,
        )

        with await main_state.authenticate_user():
            WorkingHoursService.update_settings(dto, current_user.id)

        self._load_working_hours()
        yield await toast_tr.success(self, "settings.working_hours.saved")
