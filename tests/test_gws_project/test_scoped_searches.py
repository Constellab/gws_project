from contextlib import contextmanager
from datetime import date, datetime
from unittest.mock import patch

from gws_core import (
    BaseTestCase,
    CurrentUserService,
    TestMockSpaceService,
    UnauthorizedException,
    UserGroup,
)
from gws_core import User as GwsCoreUser
from gws_project.company.company_dto import SaveCompanyDTO
from gws_project.company.company_service import CompanyService
from gws_project.project.project import Project
from gws_project.project.project_dto import SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import CreateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.user.app_role_service import AppRoleService
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user_app_role import AppRole, UserAppRole


# test_scoped_searches
class TestScopedSearches(BaseTestCase):
    """Test suite for the search entry points the app is allowed to call.

    The app passes filter values that come from the frontend (a project id, a company
    id), so these methods own the authorization: they must never return rows of a
    project the current user is not a member of, whatever the filters say.
    """

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        ProjectUserSyncService().sync_all_users()

    def _project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _create_project(self, name: str) -> Project:
        return self._project_service().create_project(
            SaveProjectDTO(
                name=name,
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )

    def _create_task(self, project: Project, title: str):
        return TaskService().create_root_task(
            project.id,
            CreateTaskDTO(
                title=title,
                start_date=date(2025, 1, 2),
                due_date=date(2025, 1, 10),
            ),
        )

    def _create_user(self, email: str) -> GwsCoreUser:
        gws_core_user = GwsCoreUser(
            email=email,
            first_name="Outside",
            last_name="User",
            group=UserGroup.USER,
        )
        gws_core_user.save()
        ProjectUserSyncService().sync_all_users()
        return gws_core_user

    @contextmanager
    def _authenticate_as(self, gws_core_user: GwsCoreUser):
        """Run the block with `gws_core_user` as the current user, then restore the previous one.

        AuthenticateUser cannot be used here: it is a no-op when a user is already
        authenticated, and the test runner always authenticates one.
        """
        previous_user = CurrentUserService.get_and_check_current_user()
        CurrentUserService.set_auth_user(gws_core_user)
        try:
            yield gws_core_user
        finally:
            CurrentUserService.set_auth_user(previous_user)

    def test_search_current_user_tasks_is_bounded_to_own_projects(self):
        """With no project filter, only the tasks of the user's own projects come back"""
        project = self._create_project("Scoped Tasks Project")
        self._create_task(project, "Owner task")

        tasks = TaskService().search_current_user_tasks(allow_subtasks=False)
        self.assertIn("Owner task", [task.title for task in tasks])

        outsider = self._create_user("outsider-tasks@example.com")
        with self._authenticate_as(outsider):
            self.assertEqual(TaskService().search_current_user_tasks(allow_subtasks=False), [])

    def test_search_current_user_tasks_refuses_a_foreign_project_filter(self):
        """An explicit project id the user is not a member of is refused, not silently used"""
        project = self._create_project("Foreign Filter Project")
        self._create_task(project, "Hidden task")

        outsider = self._create_user("outsider-filter@example.com")
        with self._authenticate_as(outsider), self.assertRaises(UnauthorizedException):
            TaskService().search_current_user_tasks(project_id=project.id)

    def test_search_current_user_tasks_honours_an_own_project_filter(self):
        """A project the user is a member of filters the search down to it"""
        first = self._create_project("Filtered Project A")
        second = self._create_project("Filtered Project B")
        self._create_task(first, "Task A")
        self._create_task(second, "Task B")

        titles = [
            task.title
            for task in TaskService().search_current_user_tasks(
                project_id=first.id, allow_subtasks=False
            )
        ]
        self.assertEqual(titles, ["Task A"])

    def test_search_current_user_projects_is_bounded_to_own_projects(self):
        """A company filter cannot widen the search beyond the user's own projects"""
        company = CompanyService().create_company(SaveCompanyDTO(name="Scoped Company"))
        project = self._create_project("Company Project")
        project.company = company.id
        project.save()

        names = [
            found.title
            for found in self._project_service().search_current_user_projects(
                company_id=company.id
            )
        ]
        self.assertIn("Company Project", names)

        outsider = self._create_user("outsider-projects@example.com")
        with self._authenticate_as(outsider):
            self.assertEqual(
                self._project_service().search_current_user_projects(company_id=company.id), []
            )

    def test_company_write_is_gated_on_the_app_role(self):
        """Creating or updating a company goes through the app-level role check"""
        company_service = CompanyService()
        current_user = CurrentUserService.get_and_check_current_user()

        # MEMBER is the default role of every real user, and it is accepted
        self.assertEqual(AppRoleService.get_role_for_user(current_user.id), AppRole.MEMBER)
        created = company_service.create_company(SaveCompanyDTO(name="Allowed Company"))
        self.assertIsNotNone(created.id)

        # An ADMIN is accepted too
        AppRoleService.set_role_for_user(current_user.id, AppRole.ADMIN)
        updated = company_service.update_company(created.id, SaveCompanyDTO(name="Admin Update"))
        self.assertEqual(updated.name, "Admin Update")
        UserAppRole.delete().where(UserAppRole.user == current_user.id).execute()

        # A user holding none of the accepted roles is refused. No such role exists today
        # (both ADMIN and MEMBER are accepted), so stand in for one by making the role
        # check fail: what this asserts is that the writes really consult it.
        with patch.object(AppRoleService, "has_one_of_roles", return_value=False):
            with self.assertRaises(UnauthorizedException):
                company_service.create_company(SaveCompanyDTO(name="Refused Company"))
            with self.assertRaises(UnauthorizedException):
                company_service.update_company(created.id, SaveCompanyDTO(name="Refused Update"))
            with self.assertRaises(UnauthorizedException):
                company_service.stage_logo(created.id, b"not-an-image", "png")
