import os

from gws_core import (
    BrickMigration,
    Logger,
    RichTextFileService,
    SqlMigrator,
    Version,
    brick_migration,
)
from peewee import CharField

from gws_project.company.company import Company
from gws_project.company.company_service import LOGO_FILE_BASE_NAME
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.document.project_file_service import ProjectFileService

# Where the logos used to live: gws_core's generic rich text image storage, under a
# directory named after the company id (data_dir/note/company_logo/{company_id}).
_OLD_LOGO_OBJECT_TYPE = "company_logo"

# The column that used to hold the name of the image file in that directory.
_OLD_LOGO_COLUMN = "logo_filename"


@brick_migration(
    "0.2.0-beta.12",
    short_description="Store company logos in the brick file store like documents",
    db_manager=ProjectDbManager.get_instance(),
)
class Migration020Beta12(BrickMigration):
    """Move company logos out of the rich-text image storage into the brick's store.

    A logo is a file of this brick, so it is now stored like every other one: the bytes
    live in the dedicated ``LocalFileStore`` and the company references the
    ``ProjectFile`` that registers them, instead of holding the bare file name of an
    image dropped in gws_core's note directory.

    Each existing image is MOVED into the store (so nothing is duplicated), the company
    is pointed at the new ``ProjectFile`` row, and the directory it came from is removed.
    A company whose image is already gone from disk simply ends up with no logo.
    """

    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        # The new column must exist before the logos can be attached to it
        sql_migrator.add_column_if_not_exists(
            Company, CharField(max_length=36, null=True), "logo_file_id"
        )
        sql_migrator.migrate()

        cls._migrate_logos()

        sql_migrator.drop_column_if_exists(Company, _OLD_LOGO_COLUMN)
        sql_migrator.migrate()

        Company.create_foreign_key_if_not_exist(Company.logo_file)

    @classmethod
    def _migrate_logos(cls) -> None:
        """Move every stored logo into the file store and attach it to its company."""
        db = ProjectDbManager.get_instance().db
        table_name = Company.get_table_name()

        # Read (and write) the old column with raw SQL: it is gone from the model, and a
        # data migration must not touch last_modified_at/last_modified_by of the rows.
        cursor = db.execute_sql(
            f"SELECT id, {_OLD_LOGO_COLUMN} FROM {table_name} "  # noqa: S608  (no user input)
            f"WHERE {_OLD_LOGO_COLUMN} IS NOT NULL AND {_OLD_LOGO_COLUMN} != ''"
        )

        for company_id, logo_filename in cursor.fetchall():
            image_path = RichTextFileService.get_object_file_path(
                _OLD_LOGO_OBJECT_TYPE, company_id, logo_filename
            )

            if not os.path.exists(image_path):
                Logger.warning(
                    f"Migration 0.2.0-beta.12: the logo of company '{company_id}' is missing "
                    f"from '{image_path}', the company is left without a logo"
                )
                continue

            extension = os.path.splitext(logo_filename)[1]
            # MOVES the image into the store, so it is never stored twice
            project_file = ProjectFileService.create_from_path(
                image_path, f"{LOGO_FILE_BASE_NAME}{extension}"
            )

            db.execute_sql(
                f"UPDATE {table_name} SET logo_file_id = %s WHERE id = %s",  # noqa: S608
                (project_file.id, company_id),
            )

            # The directory only ever held this company's logos (including the ones
            # replaced by later uploads), so it goes with them.
            RichTextFileService.delete_object_dir(_OLD_LOGO_OBJECT_TYPE, company_id)
