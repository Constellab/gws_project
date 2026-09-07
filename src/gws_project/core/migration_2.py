from gws_core import BrickMigration, SqlMigrator, Version, brick_migration
from peewee import DateField, IntegerField

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.task.task import Task
from gws_project.template.task_template import TaskTemplate


@brick_migration(
    "0.2.0-beta.6",
    short_description=(
        "Make task start_date/end_date (now due_date) and task template start_date_offset/duration_days nullable"
    ),
    db_manager=ProjectDbManager.get_instance(),
)
class Migration0206Beta6(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        # Relax the NOT NULL constraint on task dates: a task's dates are now optional
        sql_migrator.alter_column_type(Task, "start_date", DateField(null=True))
        # The due date column is only renamed from `end_date` to `due_date` in
        # 0.2.0-beta.11, so which name it answers to here depends on the version the lab
        # is upgrading from. `alter_column_type` has no "if exists" guard, so naming the
        # wrong one aborts the whole migration chain.
        due_date_column = "due_date" if Task.column_exists("due_date") else "end_date"
        sql_migrator.alter_column_type(Task, due_date_column, DateField(null=True))

        # Same for task template offset/duration: a template with no offset now
        # produces a task with no dates at all instead of defaulting to 0/1
        sql_migrator.alter_column_type(TaskTemplate, "start_date_offset", IntegerField(null=True))
        sql_migrator.alter_column_type(TaskTemplate, "duration_days", IntegerField(null=True))
        sql_migrator.migrate()
