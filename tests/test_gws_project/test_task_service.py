
from datetime import date, datetime

from gws_core import (BadRequestException, BaseTestCase, CurrentUserService,
                      TestMockSpaceService, UserGroup)
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import (CreateRootTaskDTO, CreateSubTaskDTO,
                                       TaskPriority, TaskStatus, UpdateTaskDTO)
from gws_project.task.task_service import TaskService
from gws_project.user.user import User
from gws_project.user.user_service import UserService


# test_task_service
class TestTaskService(BaseTestCase):
    """Test suite for TaskService public methods"""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        UserService.sync_gws_core_users()

    def _get_task_service(self) -> TaskService:
        """Create a TaskService instance with mock space service"""
        return TaskService(TestMockSpaceService())

    def _create_test_project(self, project_service: ProjectService) -> Project:
        """Helper method to create a test project"""
        project_dto = SaveProjectDTO(
            name='Test Project',
            description='Test Project Description',
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
        )
        return project_service.create_project(project_dto)

    def _create_test_user(self, email: str = "testuser@example.com") -> User:
        """Helper method to create a test user"""
        user = User(
            user_email=email,
            user_first_name='Test',
            user_last_name='User',
            group=UserGroup.USER,
        )
        user.save()
        return user

    def test_create_root_task(self):
        """Test create_root_task method"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        # Create test project and user
        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create root task DTO
        root_task_dto = CreateRootTaskDTO(
            title='Test Root Task',
            description='Test root task description',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            allow_subtasks=True,
            assign_to_id=current_user.id
        )

        # Test successful creation
        created_task = task_service.create_root_task(project.id, root_task_dto)

        # Assertions
        self.assertIsNotNone(created_task)
        self.assertEqual(created_task.title, 'Test Root Task')
        self.assertEqual(created_task.description, 'Test root task description')
        self.assertEqual(created_task.start_date, date(2025, 2, 1))
        self.assertEqual(created_task.end_date, date(2025, 2, 28))
        self.assertEqual(created_task.status, TaskStatus.TODO)
        self.assertEqual(created_task.priority, TaskPriority.HIGH)
        self.assertTrue(created_task.allow_subtasks)
        self.assertEqual(created_task.assign_to.id, current_user.id)
        self.assertEqual(created_task.project.id, project.id)
        self.assertIsNone(created_task.parent_task)
        self.assertTrue(created_task.is_root_task())
        self.assertIsNotNone(created_task.space_folder_id)  # Should be created in Space

    def test_create_root_task_invalid_dates(self):
        """Test create_root_task with invalid dates"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Test start date before project start date
        invalid_dto = CreateRootTaskDTO(
            title='Invalid Task',
            description='Task with invalid dates',
            start_date=date(2024, 12, 31),  # Before project start
            end_date=date(2025, 2, 28),
            assign_to_id=current_user.id
        )

        with self.assertRaises(BadRequestException) as context:
            task_service.create_root_task(project.id, invalid_dto)
        self.assertIn('start date', str(context.exception))

        # Test end date after project end date
        invalid_dto.start_date = date(2025, 2, 1)
        invalid_dto.end_date = date(2026, 1, 1)  # After project end

        with self.assertRaises(BadRequestException) as context:
            task_service.create_root_task(project.id, invalid_dto)
        self.assertIn('end date', str(context.exception))

        # Test start date after end date
        invalid_dto.start_date = date(2025, 3, 1)
        invalid_dto.end_date = date(2025, 2, 28)

        with self.assertRaises(BadRequestException) as context:
            task_service.create_root_task(project.id, invalid_dto)
        self.assertIn('start date', str(context.exception))

    def test_create_root_task_user_not_in_project(self):
        """Test create_root_task with user not in project"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        external_user = self._create_test_user("external@example.com")

        root_task_dto = CreateRootTaskDTO(
            title='Test Task',
            description='Test description',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            assign_to_id=external_user.id
        )

        with self.assertRaises(BadRequestException):
            task_service.create_root_task(project.id, root_task_dto)

    def test_create_sub_task(self):
        """Test create_sub_task method"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # First create a root task that allows subtasks
        root_task_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent task description',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # Create subtask DTO
        sub_task_dto = CreateSubTaskDTO(
            title='Test Sub Task',
            description='Test subtask description',
            start_date=date(2025, 2, 5),
            end_date=date(2025, 2, 15),
            status=TaskStatus.DOING,
            priority=TaskPriority.LOW,
            assign_to_id=current_user.id
        )

        # Test successful creation
        created_subtask = task_service.create_sub_task(root_task.id, sub_task_dto)

        # Assertions
        self.assertIsNotNone(created_subtask)
        self.assertEqual(created_subtask.title, 'Test Sub Task')
        self.assertEqual(created_subtask.description, 'Test subtask description')
        self.assertEqual(created_subtask.start_date, date(2025, 2, 5))
        self.assertEqual(created_subtask.end_date, date(2025, 2, 15))
        self.assertEqual(created_subtask.status, TaskStatus.DOING)
        self.assertEqual(created_subtask.priority, TaskPriority.LOW)
        self.assertFalse(created_subtask.allow_subtasks)  # Subtasks cannot have subtasks
        self.assertEqual(created_subtask.assign_to.id, current_user.id)
        self.assertEqual(created_subtask.project.id, project.id)
        self.assertEqual(created_subtask.parent_task.id, root_task.id)
        self.assertFalse(created_subtask.is_root_task())
        self.assertIsNone(created_subtask.space_folder_id)  # No Space folder for subtasks

    def test_create_sub_task_invalid_parent(self):
        """Test create_sub_task with invalid parent task conditions"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a root task that does NOT allow subtasks
        root_task_dto = CreateRootTaskDTO(
            title='No Subtasks Parent',
            description='Parent that does not allow subtasks',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=False,
            assign_to_id=current_user.id
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        sub_task_dto = CreateSubTaskDTO(
            title='Test Sub Task',
            description='Test subtask',
            start_date=date(2025, 2, 5),
            end_date=date(2025, 2, 15),
            assign_to_id=current_user.id
        )

        # Test failure when parent doesn't allow subtasks
        with self.assertRaises(BadRequestException) as context:
            task_service.create_sub_task(root_task.id, sub_task_dto)
        self.assertIn('does not allow subtasks', str(context.exception))

    def test_create_sub_task_invalid_dates(self):
        """Test create_sub_task with dates outside parent task bounds"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task
        root_task_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent task',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # Test start date before parent start date
        invalid_dto = CreateSubTaskDTO(
            title='Invalid Subtask',
            description='Subtask with invalid dates',
            start_date=date(2025, 1, 31),  # Before parent start
            end_date=date(2025, 2, 15),
            assign_to_id=current_user.id
        )

        with self.assertRaises(BadRequestException) as context:
            task_service.create_sub_task(root_task.id, invalid_dto)
        self.assertIn('start date', str(context.exception))

    def test_update_task(self):
        """Test update_task method"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a task to update
        root_task_dto = CreateRootTaskDTO(
            title='Original Title',
            description='Original description',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            priority=TaskPriority.MEDIUM,
            assign_to_id=current_user.id
        )
        created_task = task_service.create_root_task(project.id, root_task_dto)

        # Update task DTO
        update_dto = UpdateTaskDTO(
            title='Updated Title',
            description='Updated description',
            start_date=date(2025, 2, 5),
            end_date=date(2025, 2, 25),
            priority=TaskPriority.HIGH
        )

        # Test successful update
        updated_task = task_service.update_task(created_task.id, update_dto)

        # Assertions
        self.assertEqual(updated_task.id, created_task.id)
        self.assertEqual(updated_task.title, 'Updated Title')
        self.assertEqual(updated_task.description, 'Updated description')
        self.assertEqual(updated_task.start_date, date(2025, 2, 5))
        self.assertEqual(updated_task.end_date, date(2025, 2, 25))
        self.assertEqual(updated_task.priority, TaskPriority.HIGH)

    def test_update_assign_to(self):
        """Test update_assign_to method"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create another user and add them to the project
        second_user = self._create_test_user("second@example.com")
        project_service.add_group_to_project(project.id, second_user.id, ProjectUserRole.USER)

        # Create a task
        root_task_dto = CreateRootTaskDTO(
            title='Test Task',
            description='Test description',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            assign_to_id=current_user.id
        )
        created_task = task_service.create_root_task(project.id, root_task_dto)

        # Test successful assignment update
        updated_task = task_service.update_assign_to(created_task.id, second_user.id)

        # Assertions
        self.assertEqual(updated_task.assign_to.id, second_user.id)

        # Test assignment to user not in project
        external_user = self._create_test_user("external2@example.com")
        with self.assertRaises(BadRequestException) as context:
            task_service.update_assign_to(created_task.id, external_user.id)

    def test_update_status(self):
        """Test update_status method"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a task without subtasks
        root_task_dto = CreateRootTaskDTO(
            title='Test Task',
            description='Test description',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            status=TaskStatus.TODO,
            allow_subtasks=False,
            assign_to_id=current_user.id
        )
        created_task = task_service.create_root_task(project.id, root_task_dto)

        # Test successful status update
        updated_task = task_service.update_status(created_task.id, TaskStatus.DONE)
        self.assertEqual(updated_task.status, TaskStatus.DONE)

        # Test failure when task allows subtasks
        task_with_subtasks_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent with subtasks',
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        parent_task = task_service.create_root_task(project.id, task_with_subtasks_dto)

        with self.assertRaises(BadRequestException) as context:
            task_service.update_status(parent_task.id, TaskStatus.DONE)
        self.assertIn('subtasks', str(context.exception))

    def test_delete_task(self):
        """Test delete_task method"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a root task with subtasks
        root_task_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent task to delete',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # Create a subtask
        sub_task_dto = CreateSubTaskDTO(
            title='Sub Task',
            description='Subtask to be deleted with parent',
            start_date=date(2025, 2, 5),
            end_date=date(2025, 2, 15),
            assign_to_id=current_user.id
        )
        sub_task = task_service.create_sub_task(root_task.id, sub_task_dto)

        # Store IDs for verification
        root_task_id = root_task.id
        sub_task_id = sub_task.id

        # Test successful deletion
        task_service.delete_task(root_task_id)

        # Verify both tasks are deleted
        root_exists = Task.select().where(Task.id == root_task_id).exists()
        sub_exists = Task.select().where(Task.id == sub_task_id).exists()

        self.assertFalse(root_exists)
        self.assertFalse(sub_exists)

    def test_delete_subtask_only(self):
        """Test deleting only a subtask (not the parent)"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent and subtask
        root_task_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent task',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        sub_task_dto = CreateSubTaskDTO(
            title='Sub Task',
            description='Subtask to delete',
            start_date=date(2025, 2, 5),
            end_date=date(2025, 2, 15),
            assign_to_id=current_user.id
        )
        sub_task = task_service.create_sub_task(root_task.id, sub_task_dto)

        # Delete only the subtask
        task_service.delete_task(sub_task.id)

        # Verify subtask is deleted but parent remains
        root_exists = Task.select().where(Task.id == root_task.id).exists()
        sub_exists = Task.select().where(Task.id == sub_task.id).exists()

        self.assertTrue(root_exists)
        self.assertFalse(sub_exists)

    def test_comprehensive_task_workflow(self):
        """Test a complete workflow of task operations"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Add another user to the project
        second_user = self._create_test_user("workflow@example.com")
        project_service.add_group_to_project(project.id, second_user.id, ProjectUserRole.USER)

        # 1. Create root task with subtasks allowed
        root_task_dto = CreateRootTaskDTO(
            title='Main Development Task',
            description='Main task for development work',
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            priority=TaskPriority.HIGH,
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # 2. Create multiple subtasks
        subtask1_dto = CreateSubTaskDTO(
            title='Database Setup',
            description='Set up database schema',
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            priority=TaskPriority.HIGH,
            assign_to_id=current_user.id
        )
        subtask1 = task_service.create_sub_task(root_task.id, subtask1_dto)

        subtask2_dto = CreateSubTaskDTO(
            title='API Development',
            description='Develop REST API endpoints',
            start_date=date(2025, 3, 11),
            end_date=date(2025, 3, 20),
            priority=TaskPriority.MEDIUM,
            assign_to_id=second_user.id
        )
        subtask2 = task_service.create_sub_task(root_task.id, subtask2_dto)

        # 3. Update root task
        update_dto = UpdateTaskDTO(
            title='Enhanced Development Task',
            description='Enhanced main task description',
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 30),
            priority=TaskPriority.MEDIUM
        )
        updated_root = task_service.update_task(root_task.id, update_dto)

        # 4. Update subtask status
        task_service.update_status(subtask1.id, TaskStatus.DONE)

        # 5. Reassign subtask
        task_service.update_assign_to(subtask2.id, current_user.id)

        # Verify final state
        refreshed_root = Task.get_by_id(root_task.id)
        refreshed_subtask1 = Task.get_by_id(subtask1.id)
        refreshed_subtask2 = Task.get_by_id(subtask2.id)

        # Assertions on final state
        self.assertEqual(refreshed_root.title, 'Enhanced Development Task')
        self.assertEqual(refreshed_root.priority, TaskPriority.MEDIUM)
        self.assertEqual(refreshed_subtask1.status, TaskStatus.DONE)
        self.assertEqual(refreshed_subtask2.assign_to.id, current_user.id)

        # Clean up by deleting root task (should delete all subtasks)
        task_service.delete_task(root_task.id)

        # Verify all tasks are deleted
        self.assertFalse(Task.select().where(Task.id == root_task.id).exists())
        self.assertFalse(Task.select().where(Task.id == subtask1.id).exists())
        self.assertFalse(Task.select().where(Task.id == subtask2.id).exists())

    def test_parent_status_update_single_subtask_doing(self):
        """Test parent status updates to DOING when a single subtask is set to DOING"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task with allow_subtasks=True
        parent_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent task that allows subtasks',
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create subtask
        subtask_dto = CreateSubTaskDTO(
            title='Subtask 1',
            description='First subtask',
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id
        )
        subtask = task_service.create_sub_task(parent_task.id, subtask_dto)

        # Update subtask status to DOING
        task_service.update_status(subtask.id, TaskStatus.DOING)

        # Check that parent status is automatically updated to DOING
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.DOING)

    def test_parent_status_update_all_subtasks_done(self):
        """Test parent status updates to DONE when all subtasks are DONE"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task
        parent_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent task',
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create multiple subtasks
        subtask1_dto = CreateSubTaskDTO(
            title='Subtask 1',
            description='First subtask',
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id
        )
        subtask1 = task_service.create_sub_task(parent_task.id, subtask1_dto)

        subtask2_dto = CreateSubTaskDTO(
            title='Subtask 2',
            description='Second subtask',
            start_date=date(2025, 3, 11),
            end_date=date(2025, 3, 15),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id
        )
        subtask2 = task_service.create_sub_task(parent_task.id, subtask2_dto)

        # Update first subtask to DONE
        task_service.update_status(subtask1.id, TaskStatus.DONE)

        # Parent should still be TODO (not all subtasks are done)
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.TODO)

        # Update second subtask to DONE
        task_service.update_status(subtask2.id, TaskStatus.DONE)

        # Now parent should be DONE (all subtasks are done)
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.DONE)

    def test_parent_status_update_mixed_subtask_statuses(self):
        """Test parent status update with mixed subtask statuses"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task
        parent_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent task',
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create three subtasks
        subtask1_dto = CreateSubTaskDTO(
            title='Subtask 1',
            description='First subtask',
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 8),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id
        )
        subtask1 = task_service.create_sub_task(parent_task.id, subtask1_dto)

        subtask2_dto = CreateSubTaskDTO(
            title='Subtask 2',
            description='Second subtask',
            start_date=date(2025, 3, 9),
            end_date=date(2025, 3, 12),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id
        )
        subtask2 = task_service.create_sub_task(parent_task.id, subtask2_dto)

        subtask3_dto = CreateSubTaskDTO(
            title='Subtask 3',
            description='Third subtask',
            start_date=date(2025, 3, 13),
            end_date=date(2025, 3, 16),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id
        )
        subtask3 = task_service.create_sub_task(parent_task.id, subtask3_dto)

        # Set one subtask to DONE, one to DOING, one remains TODO
        task_service.update_status(subtask1.id, TaskStatus.DONE)
        task_service.update_status(subtask2.id, TaskStatus.DOING)
        # subtask3 remains TODO

        # Parent should be DOING (because at least one subtask is DOING)
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.DOING)

        # Now set the DOING subtask back to TODO
        task_service.update_status(subtask2.id, TaskStatus.TODO)

        # Parent should be TODO (no subtasks are DOING, not all are DONE)
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.TODO)

    def test_parent_status_update_priority_rules(self):
        """Test the priority rules: DOING > DONE > TODO"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task
        parent_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent task',
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create multiple subtasks
        subtasks = []
        for i in range(3):
            subtask_dto = CreateSubTaskDTO(
                title=f'Subtask {i+1}',
                description=f'Subtask {i+1}',
                start_date=date(2025, 3, 5+i*3),
                end_date=date(2025, 3, 7+i*3),
                status=TaskStatus.TODO,
                assign_to_id=current_user.id
            )
            subtask = task_service.create_sub_task(parent_task.id, subtask_dto)
            subtasks.append(subtask)

        # Scenario 1: Set all to DONE - parent should be DONE
        for subtask in subtasks:
            task_service.update_status(subtask.id, TaskStatus.DONE)

        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.DONE)

        # Scenario 2: Set one to DOING while others are DONE - parent should be DOING
        task_service.update_status(subtasks[0].id, TaskStatus.DOING)

        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.DOING)

        # Scenario 3: Set the DOING one back to TODO while others are DONE - parent should be TODO
        task_service.update_status(subtasks[0].id, TaskStatus.TODO)

        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.TODO)

    def test_parent_status_no_update_for_leaf_tasks(self):
        """Test that updating status of tasks without parents doesn't cause errors"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a root task without subtasks (leaf task)
        root_task_dto = CreateRootTaskDTO(
            title='Leaf Task',
            description='Task without subtasks',
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 15),
            status=TaskStatus.TODO,
            allow_subtasks=False,
            assign_to_id=current_user.id
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # Update its status - should work normally without parent updates
        updated_task = task_service.update_status(root_task.id, TaskStatus.DONE)
        self.assertEqual(updated_task.status, TaskStatus.DONE)

    def test_parent_status_update_no_subtasks(self):
        """Test parent status calculation when parent has no subtasks"""
        task_service = self._get_task_service()
        project_service = ProjectService(TestMockSpaceService())

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task that allows subtasks but has none yet
        parent_dto = CreateRootTaskDTO(
            title='Parent Task',
            description='Parent task with no subtasks',
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.DOING,
            allow_subtasks=True,
            assign_to_id=current_user.id
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # The _calculate_parent_status_from_subtasks method should return TODO for empty list
        calculated_status = task_service._calculate_parent_status_from_subtasks(parent_task)
        self.assertEqual(calculated_status, TaskStatus.TODO)
