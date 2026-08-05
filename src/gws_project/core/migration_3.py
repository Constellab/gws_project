from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project_user import ProjectUser


@brick_migration(
    "0.2.0-beta.7",
    short_description="Migrate ProjectUser rows with the removed VIEWER role to USER",
    db_manager=ProjectDbManager.get_instance(),
)
class Migration0207Beta7(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        # The VIEWER role was removed from ProjectUserRole; existing rows still holding it
        # would fail enum validation as soon as they are read back from the database.
        ProjectDbManager.get_instance().db.execute_sql(
            f"UPDATE {ProjectUser.get_table_name()} SET role = 'USER' WHERE role = 'VIEWER'"
        )
