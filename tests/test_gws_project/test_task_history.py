from datetime import date, datetime

from gws_core import BaseTestCase, CurrentUserService, RichText, TestMockSpaceService, UserGroup
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import CreateTaskDTO, TaskPriority, TaskStatus, UpdateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.task_history.task_history_event_type import TaskHistoryEventType
from gws_project.task_history.task_history_service import TaskHistoryService
from gws_project.task_history.task_history_value import TaskHistoryTaskType
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user import User


# test_task_history
class TestTaskHistory(BaseTestCase):
    """Test suite for TaskHistoryService and its integration in TaskService"""

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

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _create_test_project(self, project_service: ProjectService) -> Project:
        project_dto = SaveProjectDTO(
            name="Test Project",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
        )
        return project_service.create_project(project_dto)

    def _create_test_user(self, email: str) -> User:
        user = User(
            email=email,
            first_name="Second",
            last_name="User",
            group=UserGroup.USER,
        )
        user.save()
        return user

    def _event_types(self, task_id: str) -> list[TaskHistoryEventType]:
        events = TaskHistoryService().get_events_of_task(task_id)
        return [event.event_type for event in events]

    def test_create_root_task_logs_created(self):
        """Creating a root task logs a single CREATED event"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        task_dto = CreateTaskDTO(
            title="Root Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)

        events = TaskHistoryService().get_events_of_task(task.id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, TaskHistoryEventType.CREATED)
        self.assertEqual(events[0].actor.id, current_user.id)

    def test_update_task_logs_only_changed_fields(self):
        """update_task logs one event per field that actually changed, and no event for
        fields that keep their previous value"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        task_dto = CreateTaskDTO(
            title="Original Title",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)

        # Only the title changes: dates/status/priority/assignee are resent identical
        update_dto = UpdateTaskDTO(
            title="Updated Title",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
        )
        task_service.update_task(task.id, update_dto)

        events = TaskHistoryService().get_events_of_task(task.id)
        event_types = [event.event_type for event in events]
        self.assertEqual(event_types, [TaskHistoryEventType.CREATED, TaskHistoryEventType.TITLE_CHANGED])

        title_event = events[1]
        self.assertEqual(title_event.old_value, "Original Title")
        self.assertEqual(title_event.new_value, "Updated Title")
        self.assertFalse(title_event.is_automatic)

    def test_update_task_logs_multiple_changed_fields(self):
        """update_task logs one event for each of several fields changed at once"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        task_dto = CreateTaskDTO(
            title="Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)

        update_dto = UpdateTaskDTO(
            title="Task",
            start_date=date(2025, 2, 5),
            end_date=date(2025, 2, 25),
            status=TaskStatus.DOING,
            priority=TaskPriority.HIGH,
        )
        task_service.update_task(task.id, update_dto)

        event_types = self._event_types(task.id)
        self.assertEqual(
            event_types,
            [
                TaskHistoryEventType.CREATED,
                TaskHistoryEventType.DATES_CHANGED,
                TaskHistoryEventType.STATUS_CHANGED,
                TaskHistoryEventType.PRIORITY_CHANGED,
            ],
        )

    def test_update_assign_to_logs_assignee_changed(self):
        """update_assign_to logs an ASSIGNEE_CHANGED event with the formatted names"""
        second_user = self._create_test_user("second@example.com")
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()
        project_service.add_user_to_project(project.id, second_user.id, ProjectUserRole.USER)

        task_dto = CreateTaskDTO(
            title="Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)

        task_service.update_assign_to(task.id, second_user.id)

        events = TaskHistoryService().get_events_of_task(task.id)
        assignee_event = events[-1]
        self.assertEqual(assignee_event.event_type, TaskHistoryEventType.ASSIGNEE_CHANGED)
        self.assertEqual(assignee_event.new_value, "Second User")

    def test_update_status_logs_event_only_on_real_change(self):
        """update_status logs a STATUS_CHANGED event, but calling it with the same
        status again does not log a duplicate event"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        task_dto = CreateTaskDTO(
            title="Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            status=TaskStatus.TODO,
            allow_subtasks=False,
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)

        task_service.update_status(task.id, TaskStatus.DOING)
        self.assertEqual(
            self._event_types(task.id),
            [TaskHistoryEventType.CREATED, TaskHistoryEventType.STATUS_CHANGED],
        )

        # Calling again with the same status is a no-op: no extra event
        task_service.update_status(task.id, TaskStatus.DOING)
        self.assertEqual(
            self._event_types(task.id),
            [TaskHistoryEventType.CREATED, TaskHistoryEventType.STATUS_CHANGED],
        )

    def test_update_priority_logs_event_only_on_real_change(self):
        """update_priority logs a PRIORITY_CHANGED event only when the priority actually changes"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        task_dto = CreateTaskDTO(
            title="Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            priority=TaskPriority.MEDIUM,
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)

        task_service.update_priority(task.id, TaskPriority.HIGH)
        self.assertEqual(
            self._event_types(task.id),
            [TaskHistoryEventType.CREATED, TaskHistoryEventType.PRIORITY_CHANGED],
        )

        task_service.update_priority(task.id, TaskPriority.HIGH)
        self.assertEqual(
            self._event_types(task.id),
            [TaskHistoryEventType.CREATED, TaskHistoryEventType.PRIORITY_CHANGED],
        )

    def test_update_allow_subtasks_logs_type_changed(self):
        """Converting a leaf task to a parent task (and back) logs TYPE_CHANGED events"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        task_dto = CreateTaskDTO(
            title="Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            allow_subtasks=False,
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)

        task_service.update_allow_subtasks(task.id, True)

        events = TaskHistoryService().get_events_of_task(task.id)
        type_event = events[-1]
        self.assertEqual(type_event.event_type, TaskHistoryEventType.TYPE_CHANGED)
        self.assertEqual(type_event.new_value, TaskHistoryTaskType.PARENT.value)

    def test_move_task_logs_moved_event(self):
        """Moving a task to another project logs a MOVED event"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        source_project = self._create_test_project(project_service)
        destination_project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        task_dto = CreateTaskDTO(
            title="Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(source_project.id, task_dto)

        task_service.move_task(task.id, destination_project.id, None)

        events = TaskHistoryService().get_events_of_task(task.id)
        moved_event = events[-1]
        self.assertEqual(moved_event.event_type, TaskHistoryEventType.MOVED)
        self.assertEqual(moved_event.old_value, source_project.title)
        self.assertEqual(moved_event.new_value, destination_project.title)

    def test_update_task_description_logs_description_updated(self):
        """Updating a task's description logs a DESCRIPTION_UPDATED event"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        task_dto = CreateTaskDTO(
            title="Task",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            assign_to_id=current_user.id,
        )
        task = task_service.create_root_task(project.id, task_dto)

        task_service.update_task_description(task.id, RichText().to_dto())

        self.assertEqual(
            self._event_types(task.id),
            [TaskHistoryEventType.CREATED, TaskHistoryEventType.DESCRIPTION_UPDATED],
        )

    def test_subtask_status_change_logs_automatic_event_on_parent(self):
        """When a subtask's status change causes the parent's status to be recalculated,
        an automatic STATUS_CHANGED event is logged on the parent"""
        task_service = self._get_task_service()
        project_service = self._get_project_service()

        project = self._create_test_project(project_service)
        current_user = CurrentUserService.get_and_check_current_user()

        parent_dto = CreateTaskDTO(
            title="Parent",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status=TaskStatus.TODO,
            allow_subtasks=True,
            assign_to_id=current_user.id,
        )
        parent = task_service.create_root_task(project.id, parent_dto)

        subtask_dto = CreateTaskDTO(
            title="Subtask",
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            status=TaskStatus.TODO,
            assign_to_id=current_user.id,
        )
        # Creating the subtask already shrinks the parent's automatically-calculated
        # dates to the subtask's own dates, logging its own automatic DATES_CHANGED event
        subtask = task_service.create_sub_task(parent.id, subtask_dto)

        task_service.update_status(subtask.id, TaskStatus.DOING)

        parent_events = TaskHistoryService().get_events_of_task(parent.id)
        automatic_status_events = [
            event
            for event in parent_events
            if event.is_automatic and event.event_type == TaskHistoryEventType.STATUS_CHANGED
        ]
        self.assertEqual(len(automatic_status_events), 1)
        # Values are stored language-neutral: the app turns them into a sentence in the
        # reader's language (see the app's common/tasks/task_history_message.py).
        self.assertEqual(automatic_status_events[0].old_value, TaskStatus.TODO.value)
        self.assertEqual(automatic_status_events[0].new_value, TaskStatus.DOING.value)

        # The subtask's own event is a direct (non-automatic) action
        subtask_events = TaskHistoryService().get_events_of_task(subtask.id)
        self.assertFalse(subtask_events[-1].is_automatic)
