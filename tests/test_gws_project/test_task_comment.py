from contextlib import contextmanager
from datetime import date, datetime

from gws_core import (
    BaseTestCase,
    CurrentUserService,
    RichText,
    TestMockSpaceService,
    UnauthorizedException,
    UserGroup,
)
from gws_core import User as GwsCoreUser
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import CreateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.task_comment.task_comment import TaskComment
from gws_project.task_comment.task_comment_service import TaskCommentService
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user import User


# test_task_comment
class TestTaskComment(BaseTestCase):
    """Test suite for TaskCommentService public methods"""

    test_user: User

    @classmethod
    def init_before_test(cls):
        super().init_before_test()

        user = User(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            group=UserGroup.USER,
        )
        cls.test_user = user.save()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_task_service(self) -> TaskService:
        return TaskService()

    def _get_comment_service(self) -> TaskCommentService:
        return TaskCommentService()

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _create_test_project(self, project_service: ProjectService) -> Project:
        project_dto = SaveProjectDTO(
            name="Test Project",
            start_date=datetime(2025, 1, 1),
            due_date=datetime(2025, 12, 31),
        )
        return project_service.create_project(project_dto)

    def _create_user(self, email: str) -> tuple[GwsCoreUser, User]:
        """Create a user in the gws_core database and sync it to the gws_project one.

        Both objects are needed: authentication works on the gws_core User, while
        TaskComment references the gws_project User. The sync gives them the same id.
        """
        gws_core_user = GwsCoreUser(
            email=email,
            first_name="Second",
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

    def _plain_text_content(self, text: str):
        """Build a RichTextDTO containing a single paragraph, for use as comment content."""
        rich_text = RichText()
        rich_text.add_paragraph(text)
        return rich_text.to_dto()

    def _create_test_task(self, task_service: TaskService, project: Project) -> str:
        current_user = CurrentUserService.get_and_check_current_user()
        task_dto = CreateTaskDTO(
            title="Task",
            start_date=date(2025, 2, 1),
            due_date=date(2025, 2, 28),
            assign_to_id=current_user.id,
        )
        return task_service.create_root_task(project.id, task_dto).id

    def test_create_and_get_comments(self):
        """create_comment adds a comment, get_comments_of_task returns it ordered"""
        task_service = self._get_task_service()
        comment_service = self._get_comment_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()
        task_id = self._create_test_task(task_service, project)

        content = RichText().to_dto()
        comment = comment_service.create_comment(task_id, content)

        self.assertEqual(comment.task.id, task_id)
        self.assertEqual(comment.created_by.id, current_user.id)
        self.assertEqual(comment.last_modified_by.id, current_user.id)

        comments = comment_service.get_comments_of_task(task_id)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].id, comment.id)

    def test_comment_dto_is_edited_flag(self):
        """to_dto().is_edited is False right after creation and True after an update"""
        task_service = self._get_task_service()
        comment_service = self._get_comment_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        task_id = self._create_test_task(task_service, project)

        comment = comment_service.create_comment(task_id, RichText().to_dto())
        self.assertFalse(comment.to_dto().is_edited)

        updated_comment = comment_service.update_comment(
            comment.id, self._plain_text_content("edited content")
        )
        self.assertTrue(updated_comment.to_dto().is_edited)

    def test_author_can_update_own_comment(self):
        """The comment's author can edit their own comment"""
        task_service = self._get_task_service()
        comment_service = self._get_comment_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        task_id = self._create_test_task(task_service, project)

        comment = comment_service.create_comment(task_id, RichText().to_dto())

        updated_comment = comment_service.update_comment(
            comment.id, self._plain_text_content("updated")
        )
        self.assertEqual(updated_comment.id, comment.id)

    def test_other_user_cannot_update_comment(self):
        """A project USER who is not the comment's author cannot edit it"""
        second_gws_core_user, second_user = self._create_user("second@example.com")
        task_service = self._get_task_service()
        comment_service = self._get_comment_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        project_service.add_user_to_project(project.id, second_user.id, ProjectUserRole.USER)
        task_id = self._create_test_task(task_service, project)

        # The project's creator (current test user) is the OWNER and posts the comment
        comment = comment_service.create_comment(task_id, RichText().to_dto())

        with self._authenticate_as(second_gws_core_user), self.assertRaises(UnauthorizedException):
            comment_service.update_comment(comment.id, self._plain_text_content("x"))

    def test_project_owner_can_update_others_comment(self):
        """A project OWNER can moderate (edit) another user's comment"""
        second_gws_core_user, second_user = self._create_user("third@example.com")
        task_service = self._get_task_service()
        comment_service = self._get_comment_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        project_service.add_user_to_project(project.id, second_user.id, ProjectUserRole.USER)
        task_id = self._create_test_task(task_service, project)

        with self._authenticate_as(second_gws_core_user):
            comment = comment_service.create_comment(task_id, RichText().to_dto())

        # The current test user (project OWNER) moderates the second user's comment
        updated_comment = comment_service.update_comment(
            comment.id, self._plain_text_content("moderated")
        )
        self.assertEqual(updated_comment.id, comment.id)

    def test_deleting_task_deletes_its_comments(self):
        """Deleting a task cascades to delete its comments"""
        task_service = self._get_task_service()
        comment_service = self._get_comment_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        task_id = self._create_test_task(task_service, project)

        comment = comment_service.create_comment(task_id, RichText().to_dto())

        task_service.delete_task(task_id)

        self.assertFalse(TaskComment.select().where(TaskComment.id == comment.id).exists())
