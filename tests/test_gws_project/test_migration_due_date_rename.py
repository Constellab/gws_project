from datetime import date, datetime

from gws_core import BaseTestCase, SqlMigrator, TestMockSpaceService, Version
from gws_project.core.migration_1 import Migration0205Beta5
from gws_project.core.migration_2 import Migration0206Beta6
from gws_project.core.migration_3 import Migration0207Beta7
from gws_project.core.migration_4 import Migration0208Beta8
from gws_project.core.migration_5 import Migration0208Beta9
from gws_project.core.migration_6 import Migration020Beta10
from gws_project.core.migration_7 import Migration020Beta11
from gws_project.core.migration_8 import Migration020Beta12
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.project.project_dto import SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import CreateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_migration_due_date_rename
class TestMigrationDueDateRename(BaseTestCase):
    """A lab upgrading from before 0.2.0-beta.11 still has `end_date` columns.

    The rename to `due_date` only happens in 0.2.0-beta.11, so every migration that runs
    before it must work against a table whose column is still called `end_date`. This
    replays that upgrade path on a table put back in its pre-rename shape.
    """

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        ProjectUserSyncService().sync_all_users()

    def _downgrade_schema_to_pre_beta_11(self) -> None:
        """Put the tables back in the shape a pre-0.2.0-beta.11 lab has them."""
        db = ProjectDbManager.get_instance().db
        # `due_date` was called `end_date` until 0.2.0-beta.11
        db.execute_sql(
            f"ALTER TABLE {Task.get_table_name()} CHANGE COLUMN due_date end_date DATE NULL"
        )
        db.execute_sql(
            f"ALTER TABLE {Project.get_table_name()} CHANGE COLUMN due_date end_date DATE NULL"
        )
        # `order_index` is what 0.2.0-beta.5 adds, so it must not be there yet
        db.execute_sql(f"ALTER TABLE {Task.get_table_name()} DROP COLUMN order_index")

    def test_migration_chain_runs_on_pre_rename_schema(self):
        project_service = ProjectService(TestMockSpaceService())
        project = project_service.create_project(
            SaveProjectDTO(
                name="Upgraded project",
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )
        task_service = TaskService()
        # Same dates on both, which is exactly the tie 0.2.0-beta.5 adds order_index for
        first = task_service.create_root_task(
            project.id,
            CreateTaskDTO(
                title="First task", start_date=date(2025, 2, 1), due_date=date(2025, 2, 28)
            ),
        )
        second = task_service.create_root_task(
            project.id,
            CreateTaskDTO(
                title="Second task", start_date=date(2025, 2, 1), due_date=date(2025, 2, 28)
            ),
        )

        # created_at is a second-precision DATETIME, so two tasks created in the same test
        # tie on it. Space them explicitly: the backfill orders by created_at, and a tie
        # leaves the order up to the database.
        db = ProjectDbManager.get_instance().db
        for offset, task_id in enumerate([first.id, second.id]):
            db.execute_sql(
                f"UPDATE {Task.get_table_name()} SET created_at = %s WHERE id = %s",
                (datetime(2025, 1, 1, 10, offset), task_id),
            )

        self._downgrade_schema_to_pre_beta_11()

        # Every migration a 0.1.9 lab has pending, in the order BrickMigrator runs them
        chain = [
            ("0.2.0-beta.5", Migration0205Beta5),
            ("0.2.0-beta.6", Migration0206Beta6),
            ("0.2.0-beta.7", Migration0207Beta7),
            ("0.2.0-beta.8", Migration0208Beta8),
            ("0.2.0-beta.9", Migration0208Beta9),
            ("0.2.0-beta.10", Migration020Beta10),
            ("0.2.0-beta.11", Migration020Beta11),
            ("0.2.0-beta.12", Migration020Beta12),
        ]
        from_version = "0.1.9"
        for to_version, migration in chain:
            migration.migrate(SqlMigrator(db), Version(from_version), Version(to_version))
            from_version = to_version

        # The column ends up renamed, and the tasks are readable through the ORM again
        self.assertTrue(Task.column_exists("due_date"))
        self.assertFalse(Task.column_exists("end_date"))

        tasks = {task.id: task for task in Task.select()}
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[first.id].due_date, date(2025, 2, 28))
        # 0.2.0-beta.5 backfilled the creation order it is supposed to preserve
        self.assertLess(tasks[first.id].order_index, tasks[second.id].order_index)
