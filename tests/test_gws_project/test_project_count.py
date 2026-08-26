from datetime import date, datetime

from gws_core import (
    BaseTestCase,
    CurrentUserService,
    TestMockSpaceService,
)
from gws_project.project.project_count_dto import ChildrenCountDTO
from gws_project.project.project_dto import SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import CreateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_project_count
class TestProjectCount(BaseTestCase):
    """Test suite for project and task count methods."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _get_task_service(self) -> TaskService:
        return TaskService()

    def test_count_current_user_projects(self):
        """Test counting user projects by status (total, ongoing, done, todo)."""
        project_service = self._get_project_service()

        # Initially: no projects
        counts = project_service.count_current_user_projects()
        self.assertEqual(counts.total, 0)
        self.assertEqual(counts.ongoing, 0)
        self.assertEqual(counts.done, 0)
        self.assertEqual(counts.todo, 0)

        # Create a DRAFT project (future start date, 0 progress -> todo/draft)
        draft_project = project_service.create_project(
            SaveProjectDTO(
                name="Draft Project",
                start_date=datetime(2099, 1, 1),
                due_date=datetime(2099, 12, 31),
            )
        )

        counts = project_service.count_current_user_projects()
        self.assertEqual(counts.total, 1)
        self.assertEqual(counts.todo, 1)
        self.assertEqual(counts.ongoing, 0)
        self.assertEqual(counts.done, 0)

        # Create an ACTIVE project (past start date, 0 progress -> active)
        active_project = project_service.create_project(
            SaveProjectDTO(
                name="Active Project",
                start_date=datetime(2020, 1, 1),
                due_date=datetime(2099, 12, 31),
            )
        )

        counts = project_service.count_current_user_projects()
        self.assertEqual(counts.total, 2)
        self.assertEqual(counts.todo, 1)
        self.assertEqual(counts.ongoing, 1)
        self.assertEqual(counts.done, 0)

        # Create a COMPLETED project (progress >= 100)
        completed_project = project_service.create_project(
            SaveProjectDTO(
                name="Completed Project",
                start_date=datetime(2020, 1, 1),
                due_date=datetime(2020, 12, 31),
            )
        )
        # Set progress to 100 to mark as completed
        completed_project.progress = 100
        completed_project.save()

        counts = project_service.count_current_user_projects()
        self.assertEqual(counts.total, 3)
        self.assertEqual(counts.todo, 1)
        self.assertEqual(counts.ongoing, 1)
        self.assertEqual(counts.done, 1)

    def test_get_project_children_count(self):
        """Test getting direct children count for a project."""
        project_service = self._get_project_service()
        task_service = self._get_task_service()
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a project
        project = project_service.create_project(
            SaveProjectDTO(
                name="Count Test Project",
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )

        # Initially no children
        children_count = project_service.get_project_children_count(project.id)
        self.assertIsInstance(children_count, ChildrenCountDTO)
        self.assertEqual(children_count.subtask_count, 0)
        self.assertEqual(children_count.document_count, 0)

        # Create 2 root tasks
        task1 = task_service.create_root_task(
            project.id,
            CreateTaskDTO(
                title="Root Task 1",
                start_date=date(2025, 1, 1),
                due_date=date(2025, 6, 30),
                allow_subtasks=True,
            ),
        )
        task2 = task_service.create_root_task(
            project.id,
            CreateTaskDTO(
                title="Root Task 2",
                start_date=date(2025, 7, 1),
                due_date=date(2025, 12, 31),
            ),
        )

        children_count = project_service.get_project_children_count(project.id)
        self.assertEqual(children_count.subtask_count, 2)
        self.assertEqual(children_count.document_count, 0)

        # Create a subtask under task1 - should NOT increase project children count
        subtask = task_service.create_sub_task(
            task1.id,
            CreateTaskDTO(
                title="Subtask 1.1",
                start_date=date(2025, 1, 1),
                due_date=date(2025, 3, 31),
            ),
        )

        children_count = project_service.get_project_children_count(project.id)
        self.assertEqual(children_count.subtask_count, 2)  # Still 2 root tasks

    def test_get_task_children_count(self):
        """Test getting direct children count for a task."""
        project_service = self._get_project_service()
        task_service = self._get_task_service()
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a project
        project = project_service.create_project(
            SaveProjectDTO(
                name="Task Count Test Project",
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )

        # Create a root task that allows subtasks
        parent_task = task_service.create_root_task(
            project.id,
            CreateTaskDTO(
                title="Parent Task",
                start_date=date(2025, 1, 1),
                due_date=date(2025, 12, 31),
                allow_subtasks=True,
            ),
        )

        # Initially no children
        children_count = task_service.get_task_children_count(parent_task.id)
        self.assertIsInstance(children_count, ChildrenCountDTO)
        self.assertEqual(children_count.subtask_count, 0)
        self.assertEqual(children_count.document_count, 0)

        # Create direct subtasks
        sub1 = task_service.create_sub_task(
            parent_task.id,
            CreateTaskDTO(
                title="Subtask 1",
                start_date=date(2025, 1, 1),
                due_date=date(2025, 6, 30),
                allow_subtasks=True,
            ),
        )
        sub2 = task_service.create_sub_task(
            parent_task.id,
            CreateTaskDTO(
                title="Subtask 2",
                start_date=date(2025, 7, 1),
                due_date=date(2025, 12, 31),
            ),
        )

        children_count = task_service.get_task_children_count(parent_task.id)
        self.assertEqual(children_count.subtask_count, 2)
        self.assertEqual(children_count.document_count, 0)

        # Create a nested subtask under sub1 - should NOT increase parent_task's direct count
        nested = task_service.create_sub_task(
            sub1.id,
            CreateTaskDTO(
                title="Nested Subtask 1.1",
                start_date=date(2025, 1, 1),
                due_date=date(2025, 3, 31),
            ),
        )

        children_count = task_service.get_task_children_count(parent_task.id)
        self.assertEqual(children_count.subtask_count, 2)  # Still 2 direct subtasks

        # sub1 should have 1 direct subtask
        sub1_count = task_service.get_task_children_count(sub1.id)
        self.assertEqual(sub1_count.subtask_count, 1)

        # sub2 (leaf task) should have 0 subtasks
        sub2_count = task_service.get_task_children_count(sub2.id)
        self.assertEqual(sub2_count.subtask_count, 0)
