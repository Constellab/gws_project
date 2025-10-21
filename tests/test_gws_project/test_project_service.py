
from datetime import datetime

from gws_core import (BadRequestException, BaseTestCase, CurrentUserService,
                      TestMockSpaceService, UserGroup)
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.project.project_user import ProjectUser
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskPriority, TaskStatus
from gws_project.user.user import User
from gws_project.user.user_service import UserService


# test_project_service
class TestProjectService(BaseTestCase):

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        UserService.sync_gws_core_users()

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def test_project(self):
        """Test all public methods of ProjectService in a coherent order"""

        project_service = self._get_project_service()
        current_user = CurrentUserService.get_and_check_current_user()

        # ========== Test 1: create_project ==========
        project_dto = SaveProjectDTO(
            name='Test Project',
            description='Test Description',
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
        )

        project = project_service.create_project(project_dto)

        # Assertions on the created project
        self.assertIsNotNone(project)
        self.assertEqual(project.title, 'Test Project')
        self.assertEqual(project.description, 'Test Description')
        self.assertEqual(project.start_date, datetime(2025, 1, 1))
        self.assertEqual(project.end_date, datetime(2025, 12, 31))
        self.assertEqual(project.project_manager.id, current_user.id)
        self.assertIsNotNone(project.space_folder_id)

        # Verify that the current user is added as owner
        project_user = ProjectUser.get_by_project_and_user(project.id, current_user.id)
        self.assertEqual(project_user.role, ProjectUserRole.OWNER.value)

        # ========== Test 2: update_project ==========
        update_dto = SaveProjectDTO(
            name='Updated Project Name',
            description='Updated Description',
            start_date=datetime(2025, 2, 1),
            end_date=datetime(2025, 11, 30),
        )

        updated_project = project_service.update_project(project.id, update_dto)

        # Assertions on the updated project
        self.assertEqual(updated_project.id, project.id)
        self.assertEqual(updated_project.title, 'Updated Project Name')
        self.assertEqual(updated_project.description, 'Updated Description')
        self.assertEqual(updated_project.start_date, datetime(2025, 2, 1))
        self.assertEqual(updated_project.end_date, datetime(2025, 11, 30))
        self.assertEqual(updated_project.space_folder_id, project.space_folder_id)

        # ========== Test 3: add_user_to_project ==========
        # Create a second user for testing
        second_user = User(
            user_email='testuser2@example.com',
            user_first_name='Test',
            user_last_name='User2',
            group=UserGroup.USER,
        )
        second_user.save()

        # Add user with USER role
        added_project_user = project_service.add_group_to_project(
            project.id,
            second_user.id,
            ProjectUserRole.USER
        )

        # Assertions on added user
        self.assertIsNotNone(added_project_user)
        self.assertEqual(added_project_user.project.id, project.id)
        self.assertEqual(added_project_user.user.id, second_user.id)
        self.assertEqual(added_project_user.role, ProjectUserRole.USER.value)

        # Verify user is in project
        self.assertTrue(ProjectUser.is_user_in_project(project.id, second_user.id))

        # ========== Test 4: remove_user_from_project ==========

        # Try to remove the last owner (should fail)
        with self.assertRaises(BadRequestException) as context:
            project_service.remove_user_from_project(project.id, current_user.id)

        self.assertIn('last owner', str(context.exception).lower())

        # Add second user as owner so we can test removing a user with tasks
        project_service.add_group_to_project(
            project.id,
            second_user.id,
            ProjectUserRole.OWNER
        )

        # Create a task assigned to the second user

        task = Task()
        task.project = project
        task.title = 'Test Task'
        task.description = 'Test task for user'
        task.start_date = datetime(2025, 3, 1)
        task.end_date = datetime(2025, 3, 15)
        task.status = TaskStatus.TODO
        task.priority = TaskPriority.MEDIUM
        task.assign_to = second_user
        task.save()

        # Try to remove user with assigned tasks (should fail)
        with self.assertRaises(BadRequestException) as context:
            project_service.remove_user_from_project(project.id, second_user.id)

        self.assertIn('task', str(context.exception).lower())

        # Delete the task and try again (should succeed now)
        task.delete_instance()
        project_service.remove_user_from_project(project.id, second_user.id)
        self.assertFalse(ProjectUser.is_user_in_project(project.id, second_user.id))

        # ========== Test 5: delete_project ==========
        # Get project again to ensure we have fresh instance
        project_to_delete = Project.get_by_id(project.id)
        project_service.delete_project(project_to_delete)

        # Verify project is deleted
        project_exists = Project.select().where(Project.id == project.id).exists()
        self.assertFalse(project_exists)

    def test_create_project_with_invalid_dates(self):
        """Test create_project with invalid date range"""
        project_service = self._get_project_service()

        # Test with start date after end date
        invalid_project_dto = SaveProjectDTO(
            name='Invalid Date Project',
            description='Test invalid dates',
            start_date=datetime(2025, 12, 31),
            end_date=datetime(2025, 1, 1),
        )

        with self.assertRaises(BadRequestException) as context:
            project_service.create_project(invalid_project_dto)

        self.assertIn('start date', str(context.exception).lower())
        self.assertIn('end date', str(context.exception).lower())
