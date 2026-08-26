from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.task.task import Task

# The index peewee created for the old `Project.end_date` column. A column rename leaves the
# index in place under its old name, so it is dropped and re-added to match what a fresh
# install builds for `due_date`.
_OLD_PROJECT_END_DATE_INDEX = "gws_project_projects_end_date"
_NEW_PROJECT_DUE_DATE_INDEX = "gws_project_projects_due_date"


@brick_migration(
    "0.2.0-beta.11",
    short_description="Rename project and task end_date to due_date",
    db_manager=ProjectDbManager.get_instance(),
)
class Migration020Beta11(BrickMigration):
    """Rename the `end_date` column of projects and tasks to `due_date`.

    The field is the date the project or task is due, never the end of a range, so it is
    named after what it means. `PlanningSlot.end_datetime` is a genuine range bound and is
    left untouched.
    """

    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        sql_migrator.rename_column_if_exists(Project, "end_date", "due_date")
        sql_migrator.rename_column_if_exists(Task, "end_date", "due_date")

        # Keep the index name in step with the column it indexes
        sql_migrator.drop_index_if_exists(Project, _OLD_PROJECT_END_DATE_INDEX)
        sql_migrator.add_index_if_not_exists(
            Project, _NEW_PROJECT_DUE_DATE_INDEX, ["due_date"]
        )

        sql_migrator.migrate()
