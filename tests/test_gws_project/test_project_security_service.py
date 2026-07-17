from contextlib import contextmanager
from datetime import datetime

from gws_core import (
    BaseTestCase,
    CurrentUserService,
    NotFoundException,
    RichText,
    TestMockSpaceService,
    UnauthorizedException,
    UserGroup,
)
from gws_core import User as GwsCoreUser
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_security_service import ProjectSecurityService
from gws_project.project.project_service import ProjectService
from gws_project.project.project_user import ProjectUser
from gws_project.task.task_dto import CreateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user import User


# test_project_security_service
class TestProjectSecurityService(BaseTestCase):
    """Test suite for ProjectSecurityService: the authorization boundary of the brick.

    The other test suites all run as the project owner, so they only exercise the
    passing path. These tests cover the refusal paths: unknown project/task and
    a user without the required role.
    """

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_service(self) -> ProjectSecurityService:
        return ProjectSecurityService()

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _create_project(self, name: str) -> Project:
        return self._get_project_service().create_project(
            SaveProjectDTO(
                name=name,
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31),
            )
        )

    def _create_user(self, email: str) -> tuple[GwsCoreUser, User]:
        """Create a user in the gws_core database and sync it to the gws_project one.

        Both objects are needed: authentication works on the gws_core User, while
        the ProjectUser rows reference the gws_project User. The sync gives them
        the same id.
        """
        gws_core_user = GwsCoreUser(
            email=email,
            first_name="Outside",
            last_name="User",
            group=UserGroup.USER,
        )
        gws_core_user.save()

        ProjectUserSyncService().sync_all_users()

        return gws_core_user, User.get_by_id_and_check(gws_core_user.id)

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

    def test_get_and_check_role_for_project_unknown_project(self):
        """An unknown project ID is refused with a NotFoundException"""
        service = self._get_service()

        with self.assertRaises(NotFoundException):
            service.get_and_check_role_for_project("unknown-project-id", ProjectUserRole.USER)

    def test_get_and_check_role_for_project_owner(self):
        """The owner passes the check for every role level"""
        service = self._get_service()
        project = self._create_project("Owner Project")

        for role in [ProjectUserRole.VIEWER, ProjectUserRole.USER, ProjectUserRole.OWNER]:
            checked = service.get_and_check_role_for_project(project.id, role)
            self.assertEqual(checked.id, project.id)

    def test_get_and_check_role_for_project_non_member(self):
        """A user who is not a member of the project is refused"""
        service = self._get_service()
        project = self._create_project("Non Member Project")
        outsider, _ = self._create_user("outsider-project@example.com")

        with self._authenticate_as(outsider), self.assertRaises(UnauthorizedException):
            service.get_and_check_role_for_project(project.id, ProjectUserRole.VIEWER)

    def test_get_and_check_role_for_project_insufficient_role(self):
        """A member is refused a role above the one they hold, and granted the ones below"""
        service = self._get_service()
        project = self._create_project("Insufficient Role Project")
        viewer, project_viewer = self._create_user("viewer-project@example.com")
        ProjectUser.create_or_update(project=project, user=project_viewer, role=ProjectUserRole.VIEWER)

        with self._authenticate_as(viewer):
            # VIEWER is enough for a VIEWER check
            checked = service.get_and_check_role_for_project(project.id, ProjectUserRole.VIEWER)
            self.assertEqual(checked.id, project.id)

            # but not for USER nor OWNER
            with self.assertRaises(UnauthorizedException):
                service.get_and_check_role_for_project(project.id, ProjectUserRole.USER)
            with self.assertRaises(UnauthorizedException):
                service.get_and_check_role_for_project(project.id, ProjectUserRole.OWNER)

    def test_get_and_check_role_for_task_unknown_task(self):
        """An unknown task ID is refused with a NotFoundException"""
        service = self._get_service()

        with self.assertRaises(NotFoundException):
            service.get_and_check_role_for_task("unknown-task-id", ProjectUserRole.USER)

    def test_get_and_check_role_for_task_non_member(self):
        """A user who is not a member of the task's project is refused"""
        service = self._get_service()
        project = self._create_project("Task Security Project")
        task = TaskService().create_root_task(
            project.id,
            CreateTaskDTO(
                title="Task",
                start_date=datetime(2025, 2, 1),
                end_date=datetime(2025, 2, 10),
            ),
        )
        outsider, _ = self._create_user("outsider-task@example.com")

        # The owner passes
        checked = service.get_and_check_role_for_task(task.id, ProjectUserRole.USER)
        self.assertEqual(checked.id, task.id)

        # The outsider does not: the role is checked on the task's project
        with self._authenticate_as(outsider), self.assertRaises(UnauthorizedException):
            service.get_and_check_role_for_task(task.id, ProjectUserRole.VIEWER)

    def test_get_and_check_role_for_task_insufficient_role(self):
        """A viewer of the project is refused a USER-level check on its tasks"""
        service = self._get_service()
        project = self._create_project("Task Role Project")
        task = TaskService().create_root_task(
            project.id,
            CreateTaskDTO(
                title="Task",
                start_date=datetime(2025, 2, 1),
                end_date=datetime(2025, 2, 10),
            ),
        )
        viewer, project_viewer = self._create_user("viewer-task@example.com")
        ProjectUser.create_or_update(project=project, user=project_viewer, role=ProjectUserRole.VIEWER)

        with self._authenticate_as(viewer):
            checked = service.get_and_check_role_for_task(task.id, ProjectUserRole.VIEWER)
            self.assertEqual(checked.id, task.id)

            with self.assertRaises(UnauthorizedException):
                service.get_and_check_role_for_task(task.id, ProjectUserRole.USER)

    def test_services_refuse_non_member(self):
        """The services that wrap the security check refuse a non-member.

        This covers the read methods of ProjectService/TaskService, which are the
        callers that make the check reachable from the app.
        """
        project_service = self._get_project_service()
        task_service = TaskService()
        project = self._create_project("Service Refusal Project")
        task = task_service.create_root_task(
            project.id,
            CreateTaskDTO(
                title="Task",
                start_date=datetime(2025, 2, 1),
                end_date=datetime(2025, 2, 10),
            ),
        )
        outsider, _ = self._create_user("outsider-service@example.com")

        with self._authenticate_as(outsider):
            with self.assertRaises(UnauthorizedException):
                project_service.get_project(project.id)
            with self.assertRaises(UnauthorizedException):
                project_service.get_project_users(project.id)
            with self.assertRaises(UnauthorizedException):
                project_service.get_project_children_count(project.id)
            with self.assertRaises(UnauthorizedException):
                project_service.update_project_description(project.id, RichText().to_dto())
            with self.assertRaises(UnauthorizedException):
                project_service.delete_project(project.id)
            with self.assertRaises(UnauthorizedException):
                task_service.get_task(task.id)
            with self.assertRaises(UnauthorizedException):
                task_service.get_root_tasks_of_project(project.id)
            with self.assertRaises(UnauthorizedException):
                task_service.get_subtasks(task.id)
            with self.assertRaises(UnauthorizedException):
                task_service.get_descendants_assigned_users(task.id)

        # The project and its task are untouched by the refused calls
        self.assertTrue(Project.select().where(Project.id == project.id).exists())

    def test_delete_project_requires_owner(self):
        """delete_project requires OWNER: a plain USER member is refused"""
        project_service = self._get_project_service()
        project = self._create_project("Delete Role Project")
        member, project_member = self._create_user("member-delete@example.com")
        ProjectUser.create_or_update(project=project, user=project_member, role=ProjectUserRole.USER)

        with self._authenticate_as(member):
            # A USER can read the project...
            self.assertEqual(project_service.get_project(project.id).id, project.id)

            # ...but not delete it
            with self.assertRaises(UnauthorizedException):
                project_service.delete_project(project.id)

        self.assertTrue(Project.select().where(Project.id == project.id).exists())
