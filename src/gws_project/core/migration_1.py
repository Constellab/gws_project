from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.task.task import Task
from gws_project.template.task_template import TaskTemplate


@brick_migration(
    "0.2.0-beta.4",
    short_description="Add order_index to task and task template to preserve creation order for tied dates",
    db_manager=ProjectDbManager.get_instance(),
)
class Migration0204Beta4(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        # Add order_index column to Task and TaskTemplate tables
        sql_migrator.add_column_if_not_exists(Task, Task.order_index)
        sql_migrator.add_column_if_not_exists(TaskTemplate, TaskTemplate.order_index)
        sql_migrator.migrate()

        # Backfill order_index for existing tasks and task templates based on their creation
        # order, so already-created rows with tied dates keep their original relative order.
        all_tasks: list[Task] = list(Task.select().order_by(Task.created_at))
        for index, task in enumerate(all_tasks):
            task.order_index = index
            task.save(skip_hook=True)

        all_task_templates: list[TaskTemplate] = list(
            TaskTemplate.select().order_by(TaskTemplate.created_at)
        )
        for index, task_template in enumerate(all_task_templates):
            task_template.order_index = index
            task_template.save(skip_hook=True)
