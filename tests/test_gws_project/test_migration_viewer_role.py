from datetime import datetime

from gws_core import BaseTestCase, SqlMigrator, TestMockSpaceService, Version
from gws_project.core.migration_3 import Migration0207Beta7
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.project.project_user import ProjectUser
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_migration_viewer_role
class TestMigrationViewerRole(BaseTestCase):
    """Test suite for Migration0207Beta7: converting removed VIEWER roles to USER."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        ProjectUserSyncService().sync_all_users()

    def test_migrate_viewer_role_to_user(self):
        project_service = ProjectService(TestMockSpaceService())
        project = project_service.create_project(
            SaveProjectDTO(
                name="Viewer Migration Project",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31),
            )
        )
        member = ProjectUser.get_by_project(project.id)[0]

        # Simulate a pre-migration row still holding the removed VIEWER role.
        # Raw SQL is required here: the ORM enum field would reject 'VIEWER' outright.
        db = ProjectDbManager.get_instance().db
        db.execute_sql(
            f"UPDATE {ProjectUser.get_table_name()} SET role = 'VIEWER' WHERE id = %s",
            (member.id,),
        )

        Migration0207Beta7.migrate(SqlMigrator(db), Version("0.2.0-beta.6"), Version("0.2.0-beta.7"))

        migrated = ProjectUser.get_by_id_and_check(member.id)
        self.assertEqual(migrated.role, ProjectUserRole.USER)
