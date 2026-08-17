from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.core.working_hours_settings import WorkingHoursSettings


@brick_migration(
    "0.2.0-beta.9",
    short_description="Add weekly_hours column to working hours settings",
    db_manager=ProjectDbManager.get_instance(),
)
class Migration0208Beta9(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        sql_migrator.add_column_if_not_exists(WorkingHoursSettings, WorkingHoursSettings.weekly_hours)
        sql_migrator.migrate()
