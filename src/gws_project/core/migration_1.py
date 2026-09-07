from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.task.task import Task
from gws_project.template.task_template import TaskTemplate


@brick_migration(
    "0.2.0-beta.5",
    short_description="Add order_index to task and task template to preserve creation order for tied dates",
    db_manager=ProjectDbManager.get_instance(),
)
class Migration0205Beta5(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        # Add order_index column to Task and TaskTemplate tables
        sql_migrator.add_column_if_not_exists(Task, Task.order_index)
        sql_migrator.add_column_if_not_exists(TaskTemplate, TaskTemplate.order_index)
        sql_migrator.migrate()

        # Backfill order_index for existing tasks and task templates based on their creation
        # order, so already-created rows with tied dates keep their original relative order.
        cls._backfill_order_index(Task)
        cls._backfill_order_index(TaskTemplate)

    @classmethod
    def _backfill_order_index(cls, model_type: type[ModelWithUser]) -> None:
        """Number the rows of `model_type` by creation order.

        Raw SQL rather than the ORM: a migration reads the table as it is at this point of
        the upgrade, while the model describes the table as it will be at the end of it. A
        lab upgrading from before 0.2.0-beta.11 still calls its date column `end_date`, so
        selecting `Task` through the ORM here would look for a `due_date` that only exists
        once that later migration has run. It also keeps last_modified_at/last_modified_by
        untouched, which a data migration must not change.
        """
        db = ProjectDbManager.get_instance().db
        table_name = model_type.get_table_name()

        cursor = db.execute_sql(f"SELECT id FROM {table_name} ORDER BY created_at")  # noqa: S608

        for index, (row_id,) in enumerate(cursor.fetchall()):
            db.execute_sql(
                f"UPDATE {table_name} SET order_index = %s WHERE id = %s",  # noqa: S608
                (index, row_id),
            )
