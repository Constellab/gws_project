from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project


@brick_migration(
    "0.2.0-beta.8",
    short_description="Add optional company link to project",
    db_manager=ProjectDbManager.get_instance(),
)
class Migration0208Beta8(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        # The Company table itself is brand new and created automatically at startup.
        # Only the new nullable FK column on the existing Project table needs a migration.
        sql_migrator.add_column_if_not_exists(Project, Project.company)
        sql_migrator.migrate()
