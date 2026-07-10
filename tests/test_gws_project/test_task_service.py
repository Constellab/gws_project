from datetime import date, datetime

from gws_core import (
    BadRequestException,
    BaseTestCase,
    CurrentUserService,
    TestMockSpaceService,
    UserGroup,
)
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import CreateTaskDTO, TaskPriority, TaskStatus, UpdateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user import User


# test_task_service
class TestTaskService(BaseTestCase):
    """Test suite for TaskService public methods"""

    test_user: User
    mock_space_service: TestMockSpaceService

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
        # Sync users from gws_core to gws_project database
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_task_service(self) -> TaskService:
        """Create a TaskService instance"""
        return TaskService()

    def _get_project_service(self) -> ProjectService:
        """Create a ProjectService instance with mock space service"""
        return ProjectService(TestMockSpaceService())

    def _create_test_project(self, project_service: ProjectService) -> Project:
        """Helper method to create a test project"""
        project_dto = SaveProjectDTO(
            name="Test Project",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
        )
        return project_service.create_project(project_dto)

    def _create_test_user(self, email: str = "testuser@example.com") -> User:
        """Helper method to create a test user"""
        user = User(
            email=email,
            first_name="Test",
            last_name="User",
            group=UserGroup.USER,
        )
        user.save()
        return user

    def test_create_root_task(self):
        """Test create_root_task method"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        # Create test project and user
        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create root task DTO
        root_task_dto = CreateTaskDTO(
            title="Test Root Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )

        # Test successful creation
        created_task = task_service.create_root_task(project.id, root_task_dto)

        # Assertions
        self.assertIsNotNone(created_task)
        self.assertEqual(created_task.title, "Test Root Task")
        self.assertIsNotNone(created_task.description)  # Should have RichTextDTO
        self.assertEqual(created_task.start_date, date(2025, 2, 1))
        self.assertEqual(created_task.end_date, date(2025, 2, 28))
        self.assertEqual(created_task.status, TaskStatus.TODO)
        self.assertEqual(created_task.priority, TaskPriority.HIGH)
        self.assertTrue(created_task.allow_subtasks)
        self.assertEqual(created_task.assign_to.id, current_user.id)
        self.assertEqual(created_task.project.id, project.id)
        self.assertIsNone(created_task.parent_task)
        self.assertTrue(created_task.is_root_task())

    def test_create_root_task_invalid_dates(self):
        """Test create_root_task with invalid dates"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Test start date before project start date
        invalid_dto = CreateTaskDTO(
            title="Invalid Task",
            start_date=date(2024, 12, 31),  # Before project start
            end_date=date(2025, 2, 28),
            assign_to_id=current_user.id,
        )

        with self.assertRaises(BadRequestException) as context:
            task_service.create_root_task(project.id, invalid_dto)
        self.assertIn("start date", str(context.exception))

        # Test end date after project end date
        invalid_dto.start_date = date(2025, 2, 1)
        invalid_dto.end_date = date(2026, 1, 1)  # After project end

        with self.assertRaises(BadRequestException) as context:
            task_service.create_root_task(project.id, invalid_dto)
        self.assertIn("end date", str(context.exception))

        # Test start date after end date
        invalid_dto.start_date = date(2025, 3, 1)
        invalid_dto.end_date = date(2025, 2, 28)

        with self.assertRaises(BadRequestException) as context:
            task_service.create_root_task(project.id, invalid_dto)
        self.assertIn("start date", str(context.exception))

    def test_create_root_task_user_not_in_project(self):
        """Test create_root_task with user not in project"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        external_user = self._create_test_user("external@example.com")

        root_task_dto = CreateTaskDTO(
            title="Test Task", start_date=date(2025, 2, 1), end_date=date(2025, 2, 28), assign_to_id=external_user.id
        )

        with self.assertRaises(BadRequestException):
            task_service.create_root_task(project.id, root_task_dto)

    def test_create_sub_task(self):
        """Test create_sub_task method"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # First create a root task that allows subtasks
        root_task_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # Create subtask DTO
        sub_task_dto = CreateTaskDTO(
            title="Test Sub Task",
            start_date=date(2025, 2, 5),
            end_date=date(2025, 2, 15),
            status=TaskStatus.DOING,
            priority=TaskPriority.LOW,
            assign_to_id=current_user.id,
        )

        # Test successful creation
        created_subtask = task_service.create_sub_task(root_task.id, sub_task_dto)

        # Assertions
        self.assertIsNotNone(created_subtask)
        self.assertEqual(created_subtask.title, "Test Sub Task")
        self.assertIsNotNone(created_subtask.description)  # Should have RichTextDTO
        self.assertEqual(created_subtask.start_date, date(2025, 2, 5))
        self.assertEqual(created_subtask.end_date, date(2025, 2, 15))
        self.assertEqual(created_subtask.status, TaskStatus.DOING)
        self.assertEqual(created_subtask.priority, TaskPriority.LOW)
        self.assertFalse(created_subtask.allow_subtasks)  # Subtasks cannot have subtasks
        self.assertEqual(created_subtask.assign_to.id, current_user.id)
        self.assertEqual(created_subtask.project.id, project.id)
        self.assertEqual(created_subtask.parent_task.id, root_task.id)
        self.assertFalse(created_subtask.is_root_task())

    def test_create_sub_task_invalid_parent(self):
        """Test create_sub_task with invalid parent task conditions"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a root task that does NOT allow subtasks
        root_task_dto = CreateTaskDTO(
            title="No Subtasks Parent",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=False,
            assign_to_id=current_user.id,
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        sub_task_dto = CreateTaskDTO(
            title="Test Sub Task", start_date=date(2025, 2, 5), end_date=date(2025, 2, 15), assign_to_id=current_user.id
        )

        # Test failure when parent doesn't allow subtasks
        with self.assertRaises(BadRequestException) as context:
            task_service.create_sub_task(root_task.id, sub_task_dto)
        self.assertIn("does not allow subtasks", str(context.exception))

    def test_create_sub_task_extends_parent_dates(self):
        """Test that subtask dates can extend parent task dates automatically"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task
        root_task_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # Create subtask with dates that extend beyond parent's dates
        subtask_dto = CreateTaskDTO(
            title="Extending Subtask",
            start_date=date(2025, 1, 15),  # Before parent start
            end_date=date(2025, 3, 15),  # After parent end
            assign_to_id=current_user.id,
        )

        # Subtask creation should succeed and update parent dates automatically
        created_subtask = task_service.create_sub_task(root_task.id, subtask_dto)

        # Verify subtask was created with the specified dates
        self.assertEqual(created_subtask.start_date, date(2025, 1, 15))
        self.assertEqual(created_subtask.end_date, date(2025, 3, 15))

        # Verify parent task dates were automatically updated to encompass subtask
        refreshed_parent = Task.get_by_id(root_task.id)
        self.assertEqual(refreshed_parent.start_date, date(2025, 1, 15))
        self.assertEqual(refreshed_parent.end_date, date(2025, 3, 15))

    def test_update_task(self):
        """Test update_task method"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a task to update
        root_task_dto = CreateTaskDTO(
            title="Original Title",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            priority=TaskPriority.MEDIUM,
            assign_to_id=current_user.id,
        )
        created_task = task_service.create_root_task(project.id, root_task_dto)

        # Update task DTO
        update_dto = UpdateTaskDTO(
            title="Updated Title",
            start_date=date(2025, 2, 5),
            end_date=date(2025, 2, 25),
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
        )

        # Test successful update
        updated_task = task_service.update_task(created_task.id, update_dto)

        # Assertions
        self.assertEqual(updated_task.id, created_task.id)
        self.assertEqual(updated_task.title, "Updated Title")
        self.assertEqual(updated_task.start_date, date(2025, 2, 5))
        self.assertEqual(updated_task.end_date, date(2025, 2, 25))
        self.assertEqual(updated_task.priority, TaskPriority.HIGH)

    def test_update_assign_to(self):
        """Test update_assign_to method"""
        second_user = self._create_test_user("second@example.com")
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create another user and add them to the project
        project_service.add_user_to_project(project.id, second_user.id, ProjectUserRole.USER)

        # Create a task
        root_task_dto = CreateTaskDTO(
            title="Test Task", start_date=date(2025, 2, 1), end_date=date(2025, 2, 28), assign_to_id=current_user.id
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
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a task without subtasks
        root_task_dto = CreateTaskDTO(
            title="Test Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            status=TaskStatus.TODO,
            allow_subtasks=False,
            assign_to_id=current_user.id,
        )
        created_task = task_service.create_root_task(project.id, root_task_dto)

        # Test successful status update
        updated_task = task_service.update_status(created_task.id, TaskStatus.DONE)
        self.assertEqual(updated_task.status, TaskStatus.DONE)

        # Test failure when task allows subtasks
        task_with_subtasks_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent_task = task_service.create_root_task(project.id, task_with_subtasks_dto)

        with self.assertRaises(BadRequestException) as context:
            task_service.update_status(parent_task.id, TaskStatus.DONE)
        self.assertIn("subtasks", str(context.exception))

    def test_delete_task(self):
        """Test delete_task method"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a root task with subtasks
        root_task_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # Create a subtask
        sub_task_dto = CreateTaskDTO(
            title="Sub Task", start_date=date(2025, 2, 5), end_date=date(2025, 2, 15), assign_to_id=current_user.id
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
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent and subtask
        root_task_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        sub_task_dto = CreateTaskDTO(
            title="Sub Task", start_date=date(2025, 2, 5), end_date=date(2025, 2, 15), assign_to_id=current_user.id
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
        # Add another user to the project
        second_user = self._create_test_user("workflow@example.com")
        project_service = self._get_project_service()

        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Add another user to the project
        project_service.add_user_to_project(project.id, second_user.id, ProjectUserRole.USER)

        # 1. Create root task with subtasks allowed
        root_task_dto = CreateTaskDTO(
            title="Main Development Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            priority=TaskPriority.HIGH,
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # 2. Create multiple subtasks
        subtask1_dto = CreateTaskDTO(
            title="Database Setup",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            priority=TaskPriority.HIGH,
            assign_to_id=current_user.id,
        )
        subtask1 = task_service.create_sub_task(root_task.id, subtask1_dto)

        subtask2_dto = CreateTaskDTO(
            title="API Development",
            start_date=date(2025, 3, 11),
            end_date=date(2025, 3, 20),
            priority=TaskPriority.MEDIUM,
            assign_to_id=second_user.id,
        )
        subtask2 = task_service.create_sub_task(root_task.id, subtask2_dto)

        # 3. Update root task
        update_dto = UpdateTaskDTO(
            title="Enhanced Development Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 30),
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
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
        self.assertEqual(refreshed_root.title, "Enhanced Development Task")
        # Parent task priority is automatically calculated from subtasks (highest priority)
        # subtask1 has HIGH priority, so parent will have HIGH priority
        self.assertEqual(refreshed_root.priority, TaskPriority.HIGH)
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
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task with allow_subtasks=True
        parent_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create subtask
        subtask_dto = CreateTaskDTO(
            title="Subtask 1",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask = task_service.create_sub_task(parent_task.id, subtask_dto)

        # Update subtask status to DOING
        task_service.update_status(subtask.id, TaskStatus.DOING)

        # Check that parent status is automatically updated to DOING
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.DOING)

        # Check parent progress (1 subtask in DOING = 0% progress, only DONE counts)
        self.assertEqual(refreshed_parent.progress, 0)

        # Check project progress is updated
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 0)

    def test_parent_status_update_all_subtasks_done(self):
        """Test parent status updates to DONE when all subtasks are DONE"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task
        parent_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create multiple subtasks
        subtask1_dto = CreateTaskDTO(
            title="Subtask 1",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask1 = task_service.create_sub_task(parent_task.id, subtask1_dto)

        subtask2_dto = CreateTaskDTO(
            title="Subtask 2",
            start_date=date(2025, 3, 11),
            end_date=date(2025, 3, 15),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask2 = task_service.create_sub_task(parent_task.id, subtask2_dto)

        # Update first subtask to DONE
        task_service.update_status(subtask1.id, TaskStatus.DONE)

        # Parent should still be TODO (not all subtasks are done)
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.TODO)
        # Progress should be 50% (1 of 2 subtasks done)
        self.assertEqual(refreshed_parent.progress, 50)

        # Check project progress
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 50)

        # Update second subtask to DONE
        task_service.update_status(subtask2.id, TaskStatus.DONE)

        # Now parent should be DONE (all subtasks are done)
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.DONE)
        # Progress should be 100% (all subtasks done)
        self.assertEqual(refreshed_parent.progress, 100)

        # Check project progress is also 100%
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 100)

    def test_parent_status_update_mixed_subtask_statuses(self):
        """Test parent status update with mixed subtask statuses"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task
        parent_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create three subtasks
        subtask1_dto = CreateTaskDTO(
            title="Subtask 1",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 8),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask1 = task_service.create_sub_task(parent_task.id, subtask1_dto)

        subtask2_dto = CreateTaskDTO(
            title="Subtask 2",
            start_date=date(2025, 3, 9),
            end_date=date(2025, 3, 12),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask2 = task_service.create_sub_task(parent_task.id, subtask2_dto)

        subtask3_dto = CreateTaskDTO(
            title="Subtask 3",
            start_date=date(2025, 3, 13),
            end_date=date(2025, 3, 16),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask3 = task_service.create_sub_task(parent_task.id, subtask3_dto)

        # Set one subtask to DONE, one to DOING, one remains TODO
        task_service.update_status(subtask1.id, TaskStatus.DONE)
        task_service.update_status(subtask2.id, TaskStatus.DOING)
        # subtask3 remains TODO

        # Parent should be DOING (because at least one subtask is DOING)
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.DOING)
        # Progress: 1 DONE (100%) + 1 DOING (0%) + 1 TODO (0%) = 100/3 = 33%
        self.assertEqual(refreshed_parent.progress, 33)

        # Check project progress
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 33)

        # Now set the DOING subtask back to TODO
        task_service.update_status(subtask2.id, TaskStatus.TODO)

        # Parent should be TODO (no subtasks are DOING, not all are DONE)
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.TODO)
        # Progress: 1 DONE (100%) + 2 TODO (0%) = 100/3 = 33%
        self.assertEqual(refreshed_parent.progress, 33)

        # Check project progress
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 33)

    def test_parent_status_update_priority_rules(self):
        """Test the priority rules: DOING > DONE > TODO"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task
        parent_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create multiple subtasks
        subtasks = []
        for i in range(3):
            subtask_dto = CreateTaskDTO(
                title=f"Subtask {i + 1}",
                start_date=date(2025, 3, 5 + i * 3),
                end_date=date(2025, 3, 7 + i * 3),
                status=TaskStatus.TODO,
                assign_to_id=current_user.id,
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
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a root task without subtasks (leaf task)
        root_task_dto = CreateTaskDTO(
            title="Leaf Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 15),
            status=TaskStatus.TODO,
            allow_subtasks=False,
            assign_to_id=current_user.id,
        )
        root_task = task_service.create_root_task(project.id, root_task_dto)

        # Update its status - should work normally without parent updates
        updated_task = task_service.update_status(root_task.id, TaskStatus.DONE)
        self.assertEqual(updated_task.status, TaskStatus.DONE)

    def test_parent_status_update_no_subtasks(self):
        """Test parent status when parent has no subtasks"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task that allows subtasks but has none yet
        parent_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.DOING,
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # When a task has no subtasks, it should maintain its initial status
        self.assertEqual(parent_task.status, TaskStatus.DOING)

    def test_delete_task_recalculates_parent_progress(self):
        """Test that deleting a subtask recalculates parent progress"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent task with subtasks
        parent_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create 3 subtasks
        subtask1_dto = CreateTaskDTO(
            title="Subtask 1",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask1 = task_service.create_sub_task(parent_task.id, subtask1_dto)

        subtask2_dto = CreateTaskDTO(
            title="Subtask 2",
            start_date=date(2025, 3, 11),
            end_date=date(2025, 3, 15),
            status=TaskStatus.DONE,
            assign_to_id=current_user.id,
        )
        subtask2 = task_service.create_sub_task(parent_task.id, subtask2_dto)

        subtask3_dto = CreateTaskDTO(
            title="Subtask 3",
            start_date=date(2025, 3, 16),
            end_date=date(2025, 3, 20),
            status=TaskStatus.DONE,
            assign_to_id=current_user.id,
        )
        subtask3 = task_service.create_sub_task(parent_task.id, subtask3_dto)

        # Initial state: 2 DONE, 1 TODO = 2/3 = 66% progress
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.progress, 66)

        # Check project progress
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 66)

        # Delete one DONE subtask
        task_service.delete_task(subtask2.id)

        # After deletion: 1 DONE, 1 TODO = 1/2 = 50% progress
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.progress, 50)

        # Check project progress is updated
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 50)

        # Delete the TODO subtask
        task_service.delete_task(subtask1.id)

        # After deletion: 1 DONE, 0 TODO = 1/1 = 100% progress
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.progress, 100)
        self.assertEqual(refreshed_parent.status, TaskStatus.DONE)

        # Check project progress is 100%
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 100)

        # Delete the last subtask
        task_service.delete_task(subtask3.id)

        # After deletion: No subtasks = progress is set to 0%, status should be TODO
        refreshed_parent = Task.get_by_id(parent_task.id)
        self.assertEqual(refreshed_parent.progress, 0)
        self.assertEqual(refreshed_parent.status, TaskStatus.TODO)

        # Check project progress
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 0)

    def test_progress_calculation_and_project_update(self):
        """Test progress calculation on tasks and propagation to project"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create two root tasks with subtasks
        # Root Task 1
        root1_dto = CreateTaskDTO(
            title="Backend Development",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        root1 = task_service.create_root_task(project.id, root1_dto)

        # Create 2 subtasks for root1
        subtask1_1_dto = CreateTaskDTO(
            title="Database Schema",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 10),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask1_1 = task_service.create_sub_task(root1.id, subtask1_1_dto)

        subtask1_2_dto = CreateTaskDTO(
            title="API Endpoints",
            start_date=date(2025, 2, 11),
            end_date=date(2025, 2, 20),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask1_2 = task_service.create_sub_task(root1.id, subtask1_2_dto)

        # Root Task 2
        root2_dto = CreateTaskDTO(
            title="Frontend Development",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        root2 = task_service.create_root_task(project.id, root2_dto)

        # Create 2 subtasks for root2
        subtask2_1_dto = CreateTaskDTO(
            title="UI Components",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 15),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask2_1 = task_service.create_sub_task(root2.id, subtask2_1_dto)

        subtask2_2_dto = CreateTaskDTO(
            title="State Management",
            start_date=date(2025, 3, 16),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        subtask2_2 = task_service.create_sub_task(root2.id, subtask2_2_dto)

        # Initial state: All tasks are TODO, progress should be 0
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 0)

        # Scenario 1: Complete one subtask from root1
        task_service.update_status(subtask1_1.id, TaskStatus.DONE)

        # Root1 progress: 1 DONE + 1 TODO = 50%
        refreshed_root1 = Task.get_by_id(root1.id)
        self.assertEqual(refreshed_root1.progress, 50)

        # Root2 progress: 2 TODO = 0%
        refreshed_root2 = Task.get_by_id(root2.id)
        self.assertEqual(refreshed_root2.progress, 0)

        # Project progress: average of root tasks = (50 + 0) / 2 = 25%
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 25)

        # Scenario 2: Set one subtask from root1 to DOING and one from root2 to DOING
        task_service.update_status(subtask1_2.id, TaskStatus.DOING)
        task_service.update_status(subtask2_1.id, TaskStatus.DOING)

        # Root1 progress: 1 DONE (100%) + 1 DOING (0%) = 50%
        refreshed_root1 = Task.get_by_id(root1.id)
        self.assertEqual(refreshed_root1.progress, 50)

        # Root2 progress: 1 DOING (0%) + 1 TODO (0%) = 0%
        refreshed_root2 = Task.get_by_id(root2.id)
        self.assertEqual(refreshed_root2.progress, 0)

        # Project progress: (50 + 0) / 2 = 25%
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 25)

        # Scenario 3: Complete all subtasks
        task_service.update_status(subtask1_2.id, TaskStatus.DONE)
        task_service.update_status(subtask2_1.id, TaskStatus.DONE)
        task_service.update_status(subtask2_2.id, TaskStatus.DONE)

        # Both root tasks should be 100%
        refreshed_root1 = Task.get_by_id(root1.id)
        self.assertEqual(refreshed_root1.progress, 100)
        self.assertEqual(refreshed_root1.status, TaskStatus.DONE)

        refreshed_root2 = Task.get_by_id(root2.id)
        self.assertEqual(refreshed_root2.progress, 100)
        self.assertEqual(refreshed_root2.status, TaskStatus.DONE)

        # Project progress should be 100%
        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.progress, 100)

    def test_update_allow_subtasks_leaf_to_parent(self):
        """Test converting a normal task (leaf) to a parent task (allow_subtasks=True).
        Properties should be reset to empty-parent defaults."""
        task_service = self._get_task_service()
        project_service = self._get_project_service()
        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a leaf task with specific values
        task_dto = CreateTaskDTO(
            title="Leaf Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 15),
            status=TaskStatus.DOING,
            priority=TaskPriority.HIGH,
            allow_subtasks=False,
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)
        self.assertFalse(task.allow_subtasks)
        self.assertEqual(task.status, TaskStatus.DOING)
        self.assertEqual(task.priority, TaskPriority.HIGH)

        # Convert to parent task
        updated_task = task_service.update_allow_subtasks(task.id, True)

        # Verify conversion
        self.assertTrue(updated_task.allow_subtasks)
        # Properties should be reset to empty-parent defaults
        self.assertEqual(updated_task.status, TaskStatus.TODO)
        self.assertEqual(updated_task.priority, TaskPriority.MEDIUM)
        self.assertEqual(updated_task.start_date, project.start_date.date())
        self.assertEqual(updated_task.end_date, project.end_date.date())
        self.assertEqual(updated_task.progress, 0)

        # Verify subtask creation now works
        sub_dto = CreateTaskDTO(
            title="New Subtask",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            assign_to_id=current_user.id,
        )
        subtask = task_service.create_sub_task(updated_task.id, sub_dto)
        self.assertIsNotNone(subtask)

    def test_update_allow_subtasks_parent_to_leaf_no_subtasks(self):
        """Test converting a parent task to a leaf task when it has no subtasks"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()
        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a parent task with no subtasks
        task_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)
        self.assertTrue(task.allow_subtasks)

        # Convert to leaf task
        updated_task = task_service.update_allow_subtasks(task.id, False)

        # Verify conversion
        self.assertFalse(updated_task.allow_subtasks)
        self.assertEqual(updated_task.progress, 0)  # TODO -> progress 0

        # Verify manual status update now works (was blocked for parent tasks)
        updated_task = task_service.update_status(updated_task.id, TaskStatus.DONE)
        self.assertEqual(updated_task.status, TaskStatus.DONE)

    def test_update_allow_subtasks_parent_to_leaf_with_subtasks_fails(self):
        """Test that converting a parent task to leaf fails if it has existing subtasks"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()
        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a parent task
        parent_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent_task = task_service.create_root_task(project.id, parent_dto)

        # Create a subtask
        sub_dto = CreateTaskDTO(
            title="Subtask",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            assign_to_id=current_user.id,
        )
        task_service.create_sub_task(parent_task.id, sub_dto)

        # Try to convert to leaf - should fail
        with self.assertRaises(BadRequestException) as context:
            task_service.update_allow_subtasks(parent_task.id, False)
        self.assertIn("existing subtasks", str(context.exception))

        # Verify task is still a parent
        refreshed = Task.get_by_id(parent_task.id)
        self.assertTrue(refreshed.allow_subtasks)

    def test_update_allow_subtasks_no_op_same_value(self):
        """Test that calling update_allow_subtasks with the same value is a no-op"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()
        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        task_dto = CreateTaskDTO(
            title="Leaf Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 15),
            allow_subtasks=False,
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)

        # No-op call
        result = task_service.update_allow_subtasks(task.id, False)
        self.assertFalse(result.allow_subtasks)
        self.assertEqual(result.id, task.id)

    def test_update_allow_subtasks_parent_to_leaf_progress_done(self):
        """Test progress adjustment when converting a parent with TODO status to leaf,
        then verify DONE status gives progress 100"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()
        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create parent, add subtask, complete it, delete it
        parent_dto = CreateTaskDTO(
            title="Parent Task",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent = task_service.create_root_task(project.id, parent_dto)

        sub_dto = CreateTaskDTO(
            title="Subtask",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            assign_to_id=current_user.id,
        )
        subtask = task_service.create_sub_task(parent.id, sub_dto)
        task_service.update_status(subtask.id, TaskStatus.DONE)

        # Delete the subtask - parent resets to TODO/0 via update_from_subtasks
        task_service.delete_task(subtask.id)

        refreshed_parent = Task.get_by_id(parent.id)
        self.assertEqual(refreshed_parent.status, TaskStatus.TODO)

        # Convert to leaf - progress should be 0 (status is TODO)
        updated = task_service.update_allow_subtasks(parent.id, False)
        self.assertFalse(updated.allow_subtasks)
        self.assertEqual(updated.progress, 0)

        # Set status to DONE and verify progress
        updated = task_service.update_status(updated.id, TaskStatus.DONE)
        self.assertEqual(updated.progress, 100)

    def test_update_allow_subtasks_subtask_propagates_to_ancestors(self):
        """Test that changing allow_subtasks on a nested task propagates to ancestors"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()
        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        # Create grandparent (allows subtasks)
        grandparent_dto = CreateTaskDTO(
            title="Grandparent",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        grandparent = task_service.create_root_task(project.id, grandparent_dto)

        # Create child as leaf task
        child_dto = CreateTaskDTO(
            title="Child (leaf)",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            allow_subtasks=False,
            assign_to_id=current_user.id,
        )
        child = task_service.create_sub_task(grandparent.id, child_dto)
        self.assertFalse(child.allow_subtasks)

        # Convert child to parent
        child = task_service.update_allow_subtasks(child.id, True)
        self.assertTrue(child.allow_subtasks)

        # Now add a subtask to the converted child and mark it DONE
        grandchild_dto = CreateTaskDTO(
            title="Grandchild",
            start_date=date(2025, 3, 6),
            end_date=date(2025, 3, 10),
            assign_to_id=current_user.id,
        )
        grandchild = task_service.create_sub_task(child.id, grandchild_dto)
        task_service.update_status(grandchild.id, TaskStatus.DONE)

        # Verify propagation: child should be DONE (100%), grandparent should reflect it
        refreshed_child = Task.get_by_id(child.id)
        self.assertEqual(refreshed_child.status, TaskStatus.DONE)
        self.assertEqual(refreshed_child.progress, 100)

        refreshed_grandparent = Task.get_by_id(grandparent.id)
        self.assertEqual(refreshed_grandparent.progress, 100)
        self.assertEqual(refreshed_grandparent.status, TaskStatus.DONE)
