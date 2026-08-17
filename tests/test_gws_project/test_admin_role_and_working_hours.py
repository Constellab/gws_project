from contextlib import contextmanager

from gws_core import BaseTestCase, CurrentUserService, UnauthorizedException, UserGroup
from gws_core import User as GwsCoreUser
from gws_project.core.working_hours_service import WorkingHoursService
from gws_project.core.working_hours_settings_dto import WorkingHoursSettingsDTO
from gws_project.user.app_role_service import AppRoleService
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user_app_role import AppRole


# test_admin_role_and_working_hours
class TestAdminRoleAndWorkingHours(BaseTestCase):
    """Test suite for the new, independent AppRole system and the global
    working hours settings gated by it.

    The key behavior under test is that AppRole is fully decoupled from
    gws_core's UserGroup: a lab-wide UserGroup.ADMIN must NOT automatically
    grant the new app-level Admin role, and vice versa.
    """

    def _create_user(self, email: str, group: UserGroup = UserGroup.USER) -> GwsCoreUser:
        gws_core_user = GwsCoreUser(
            email=email,
            first_name="Test",
            last_name="User",
            group=group,
        )
        gws_core_user.save()
        ProjectUserSyncService().sync_all_users()
        return gws_core_user

    @contextmanager
    def _authenticate_as(self, gws_core_user: GwsCoreUser):
        previous_user = CurrentUserService.get_and_check_current_user()
        CurrentUserService.set_auth_user(gws_core_user)
        try:
            yield gws_core_user
        finally:
            CurrentUserService.set_auth_user(previous_user)

    def test_default_role_is_member(self):
        """A user never explicitly assigned an app role defaults to MEMBER."""
        user = self._create_user("member-default@test.com")

        self.assertEqual(AppRoleService.get_role_for_user(user.id), AppRole.MEMBER)
        self.assertFalse(AppRoleService.is_admin(user.id))

    def test_app_role_independent_from_gws_core_group(self):
        """A gws_core lab-wide ADMIN must NOT be an app Admin by default, and
        an app Admin promotion must not touch the gws_core group."""
        lab_admin = self._create_user("lab-admin@test.com", group=UserGroup.ADMIN)

        # Lab-wide admin, but no app role assigned yet: still a MEMBER here.
        self.assertFalse(AppRoleService.is_admin(lab_admin.id))

        # Promote to app Admin.
        AppRoleService.set_role_for_user(lab_admin.id, AppRole.ADMIN)
        self.assertTrue(AppRoleService.is_admin(lab_admin.id))

        # The gws_core group is untouched by the app-role promotion.
        refreshed = GwsCoreUser.get_by_id_and_check(lab_admin.id)
        self.assertEqual(refreshed.group, UserGroup.ADMIN)

    def test_set_role_for_user_updates_existing_role(self):
        user = self._create_user("promote-demote@test.com")

        AppRoleService.set_role_for_user(user.id, AppRole.ADMIN)
        self.assertEqual(AppRoleService.get_role_for_user(user.id), AppRole.ADMIN)

        AppRoleService.set_role_for_user(user.id, AppRole.MEMBER)
        self.assertEqual(AppRoleService.get_role_for_user(user.id), AppRole.MEMBER)

    def test_working_hours_get_settings_creates_default_singleton(self):
        settings = WorkingHoursService.get_settings()

        self.assertEqual(settings.working_days, [0, 1, 2, 3, 4])
        self.assertEqual(settings.weekly_hours, 35.0)
        self.assertEqual(settings.timezone, "Europe/Paris")

        # A second call reuses the same row rather than creating a new one.
        settings_again = WorkingHoursService.get_settings()
        self.assertEqual(settings.id, settings_again.id)

    def test_working_hours_update_requires_app_admin(self):
        """A non-admin (app role), even a gws_core lab-wide admin, is refused."""
        member = self._create_user("member-wh@test.com")
        lab_admin_only = self._create_user("lab-admin-wh@test.com", group=UserGroup.ADMIN)
        app_admin = self._create_user("app-admin-wh@test.com")
        AppRoleService.set_role_for_user(app_admin.id, AppRole.ADMIN)

        dto = WorkingHoursSettingsDTO(
            working_days=[0, 1, 2, 3, 4, 5],
            weekly_hours=39.5,
            timezone="UTC",
            day_start_time="08:00",
            day_end_time="17:00",
            lunch_start_time="12:30",
            lunch_end_time="13:30",
        )

        with self.assertRaises(UnauthorizedException):
            WorkingHoursService.update_settings(dto, member.id)

        with self.assertRaises(UnauthorizedException):
            WorkingHoursService.update_settings(dto, lab_admin_only.id)

        updated = WorkingHoursService.update_settings(dto, app_admin.id)
        self.assertEqual(updated.timezone, "UTC")
        self.assertEqual(updated.working_days, [0, 1, 2, 3, 4, 5])
        self.assertEqual(updated.weekly_hours, 39.5)

        # The update is global: fetching settings again reflects the same values.
        self.assertEqual(WorkingHoursService.get_settings().timezone, "UTC")
