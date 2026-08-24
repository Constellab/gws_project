from datetime import date, datetime

from gws_core import (
    BaseTestCase,
    CurrentUserService,
    SqlMigrator,
    TestMockSpaceService,
    Version,
)
from gws_project.core.migration_6 import Migration020Beta10
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project_dto import SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import CreateTaskDTO, TaskPriority, TaskStatus
from gws_project.task.task_service import TaskService
from gws_project.task_history.task_history_event import TaskHistoryEvent
from gws_project.task_history.task_history_event_type import TaskHistoryEventType
from gws_project.task_history.task_history_service import TaskHistoryService
from gws_project.task_history.task_history_value import TaskHistoryTaskType
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_migration_history_values
class TestMigrationHistoryValues(BaseTestCase):
    """Test suite for Migration020Beta10: rewriting the English texts old history rows hold.

    Rows written before the history became translatable stored their values already
    formatted in English. The migration converts the vocabularies the app now translates
    (status, priority, task type, date range) and must leave free text untouched.
    """

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        ProjectUserSyncService().sync_all_users()

    def _create_task(self):
        project = ProjectService(TestMockSpaceService()).create_project(
            SaveProjectDTO(
                name="History Migration Project",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31),
            )
        )
        return TaskService().create_root_task(
            project.id,
            CreateTaskDTO(
                title="Task",
                start_date=date(2025, 2, 1),
                end_date=date(2025, 2, 28),
                assign_to_id=CurrentUserService.get_and_check_current_user().id,
            ),
        )

    def _log_legacy_event(
        self, task, event_type: TaskHistoryEventType, old_value: str, new_value: str
    ) -> TaskHistoryEvent:
        """Write a row the way a previous version of the brick would have."""
        return TaskHistoryService().log(task, event_type, old_value, new_value)

    def _run_migration(self) -> None:
        Migration020Beta10.migrate(
            SqlMigrator(ProjectDbManager.get_instance().db),
            Version("0.2.0-beta.9"),
            Version("0.2.0-beta.10"),
        )

    def test_status_and_priority_become_enum_values(self):
        task = self._create_task()
        status_event = self._log_legacy_event(
            task, TaskHistoryEventType.STATUS_CHANGED, "Todo", "Doing"
        )
        priority_event = self._log_legacy_event(
            task, TaskHistoryEventType.PRIORITY_CHANGED, "Medium", "High"
        )

        self._run_migration()

        migrated_status = TaskHistoryEvent.get_by_id_and_check(status_event.id)
        self.assertEqual(migrated_status.old_value, TaskStatus.TODO.value)
        self.assertEqual(migrated_status.new_value, TaskStatus.DOING.value)

        migrated_priority = TaskHistoryEvent.get_by_id_and_check(priority_event.id)
        self.assertEqual(migrated_priority.old_value, TaskPriority.MEDIUM.value)
        self.assertEqual(migrated_priority.new_value, TaskPriority.HIGH.value)

    def test_task_type_becomes_a_neutral_value(self):
        task = self._create_task()
        event = self._log_legacy_event(
            task, TaskHistoryEventType.TYPE_CHANGED, "a normal task", "a task with subtasks"
        )

        self._run_migration()

        migrated = TaskHistoryEvent.get_by_id_and_check(event.id)
        self.assertEqual(migrated.old_value, TaskHistoryTaskType.LEAF.value)
        self.assertEqual(migrated.new_value, TaskHistoryTaskType.PARENT.value)

    def test_date_range_becomes_iso(self):
        task = self._create_task()
        event = self._log_legacy_event(
            task,
            TaskHistoryEventType.DATES_CHANGED,
            "Feb 01, 2025 → Feb 28, 2025",
            # A range that was missing its end date
            "Mar 03, 2025 → —",
        )

        self._run_migration()

        migrated = TaskHistoryEvent.get_by_id_and_check(event.id)
        self.assertEqual(migrated.old_value, "2025-02-01|2025-02-28")
        self.assertEqual(migrated.new_value, "2025-03-03|")

    def test_free_text_and_unreadable_values_are_left_alone(self):
        task = self._create_task()
        title_event = self._log_legacy_event(
            task, TaskHistoryEventType.TITLE_CHANGED, "Old title", "New title"
        )
        # A date range this migration cannot parse must survive as it is rather than be lost
        unreadable_event = self._log_legacy_event(
            task, TaskHistoryEventType.DATES_CHANGED, "whenever → someday", "still → unknown"
        )

        self._run_migration()

        migrated_title = TaskHistoryEvent.get_by_id_and_check(title_event.id)
        self.assertEqual(migrated_title.old_value, "Old title")
        self.assertEqual(migrated_title.new_value, "New title")

        migrated_unreadable = TaskHistoryEvent.get_by_id_and_check(unreadable_event.id)
        self.assertEqual(migrated_unreadable.old_value, "whenever → someday")
        self.assertEqual(migrated_unreadable.new_value, "still → unknown")

    def test_migration_is_idempotent(self):
        task = self._create_task()
        # A row already written by the current version
        event = self._log_legacy_event(
            task, TaskHistoryEventType.STATUS_CHANGED, TaskStatus.TODO.value, TaskStatus.DONE.value
        )

        self._run_migration()
        self._run_migration()

        migrated = TaskHistoryEvent.get_by_id_and_check(event.id)
        self.assertEqual(migrated.old_value, TaskStatus.TODO.value)
        self.assertEqual(migrated.new_value, TaskStatus.DONE.value)
