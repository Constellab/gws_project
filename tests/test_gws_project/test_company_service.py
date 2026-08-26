import io
import os

from gws_core import (
    BadRequestException,
    BaseTestCase,
    CurrentUserService,
    NotFoundException,
    RichTextFileService,
)
from gws_project.company.company import Company
from gws_project.company.company_dto import CompanyStatus, SaveCompanyDTO
from gws_project.company.company_search_builder import CompanySearchBuilder
from gws_project.company.company_service import CompanyService
from gws_project.core.migration_8 import (
    _OLD_LOGO_COLUMN,
    _OLD_LOGO_OBJECT_TYPE,
    Migration020Beta12,
)
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.document.project_file import ProjectFile
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from PIL import Image


def _make_png_bytes(color: str = "red") -> bytes:
    """Build a tiny in-memory PNG, for logo upload tests."""
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color=color).save(buffer, format="PNG")
    return buffer.getvalue()


# test_company_service
class TestCompanyService(BaseTestCase):
    """Test suite for CompanyService: create/update/get/search and logo upload.

    There is intentionally no test for a "delete_company" method: companies can
    never be deleted, so no such method exists on the service (see
    test_no_delete_method).
    """

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_company_service(self) -> CompanyService:
        return CompanyService()

    def test_create_company_with_all_fields(self):
        """Test creating a company with every optional field set."""
        service = self._get_company_service()
        current_user = CurrentUserService.get_and_check_current_user()

        company = service.create_company(
            SaveCompanyDTO(
                name="Full Company",
                address="1 rue de la Paix, Paris",
                siren="123456789",
                phone="+33123456789",
                status=CompanyStatus.CLIENT,
            )
        )

        self.assertEqual(company.name, "Full Company")
        self.assertEqual(company.address, "1 rue de la Paix, Paris")
        self.assertEqual(company.siren, "123456789")
        self.assertEqual(company.phone, "+33123456789")
        self.assertEqual(company.status, CompanyStatus.CLIENT)
        self.assertIsNone(company.logo_file)
        self.assertEqual(company.created_by.id, current_user.id)
        self.assertEqual(company.last_modified_by.id, current_user.id)

        dto = company.to_dto()
        self.assertEqual(dto.name, "Full Company")
        self.assertEqual(dto.status, CompanyStatus.CLIENT)
        self.assertFalse(dto.has_logo)

    def test_create_company_name_only(self):
        """Test that every field except name is optional and defaults sensibly."""
        service = self._get_company_service()

        company = service.create_company(SaveCompanyDTO(name="Minimal Company"))

        self.assertEqual(company.name, "Minimal Company")
        self.assertIsNone(company.address)
        self.assertIsNone(company.siren)
        self.assertIsNone(company.phone)
        self.assertIsNone(company.logo_file)
        self.assertEqual(company.status, CompanyStatus.PROSPECT)

    def test_create_company_with_staged_logo(self):
        """Test that create_company attaches a logo staged before it existed."""
        service = self._get_company_service()
        logo_file = service.stage_logo(_make_png_bytes(), "png")

        company = service.create_company(
            SaveCompanyDTO(name="Staged Logo Company", logo_file_id=logo_file.id)
        )

        self.assertEqual(company.logo_file.id, logo_file.id)
        self.assertTrue(Company.get_by_id_and_check(company.id).to_dto().has_logo)

    def test_create_company_with_unknown_logo_file_id(self):
        """Test that create_company refuses a logo id that references nothing."""
        service = self._get_company_service()

        with self.assertRaises(BadRequestException):
            service.create_company(
                SaveCompanyDTO(
                    name="Lost Logo Company",
                    logo_file_id="11111111-2222-3333-4444-555555555555",
                )
            )

    def test_update_company(self):
        """Test updating a company's fields."""
        service = self._get_company_service()
        company = service.create_company(SaveCompanyDTO(name="Original Name"))

        updated = service.update_company(
            company.id,
            SaveCompanyDTO(
                name="Renamed Company",
                address="New address",
                siren="987654321",
                phone="0102030405",
                status=CompanyStatus.PARTENAIRE,
            ),
        )

        self.assertEqual(updated.name, "Renamed Company")
        self.assertEqual(updated.address, "New address")
        self.assertEqual(updated.siren, "987654321")
        self.assertEqual(updated.phone, "0102030405")
        self.assertEqual(updated.status, CompanyStatus.PARTENAIRE)

        # Persisted, not just returned in memory
        refetched = service.get_company(company.id)
        self.assertEqual(refetched.name, "Renamed Company")
        self.assertEqual(refetched.status, CompanyStatus.PARTENAIRE)

    def test_update_company_omitted_fields_are_cleared(self):
        """update_company always overwrites every field from the DTO: fields left
        out of a later update are cleared, not preserved (same behavior as
        ProjectService.update_project's handling of `company_id`)."""
        service = self._get_company_service()
        company = service.create_company(
            SaveCompanyDTO(name="Has Address", address="Some address")
        )
        self.assertEqual(company.address, "Some address")

        updated = service.update_company(company.id, SaveCompanyDTO(name="Has Address"))

        self.assertIsNone(updated.address)

    def test_get_company_not_found(self):
        """Test that get_company raises NotFoundException for an unknown id."""
        service = self._get_company_service()

        with self.assertRaises(NotFoundException):
            service.get_company("not-a-real-id")

    def test_no_delete_method(self):
        """A company can never be deleted: there must be no delete method on the
        service to accidentally call."""
        self.assertFalse(hasattr(CompanyService, "delete_company"))

    def test_search_companies_by_text(self):
        """Test filtering companies by a text search on their name."""
        service = self._get_company_service()
        service.create_company(SaveCompanyDTO(name="Acme Robotics"))
        service.create_company(SaveCompanyDTO(name="Acme Biotech"))
        service.create_company(SaveCompanyDTO(name="Globex Corp"))

        results = service.search_companies(search_text="Acme")

        self.assertEqual({c.name for c in results}, {"Acme Robotics", "Acme Biotech"})

    def test_search_companies_by_status(self):
        """Test filtering companies by status.

        Scoped with distinctive names and assertIn/assertNotIn rather than exact
        set equality: tests in this suite share the same database (no per-test
        rollback), so other tests' companies with the same status may also be
        present in the results.
        """
        service = self._get_company_service()
        service.create_company(
            SaveCompanyDTO(name="Status Filter Client Co", status=CompanyStatus.CLIENT)
        )
        service.create_company(
            SaveCompanyDTO(name="Status Filter Prospect Co", status=CompanyStatus.PROSPECT)
        )

        results = service.search_companies(status=CompanyStatus.CLIENT)
        names = {c.name for c in results}

        self.assertIn("Status Filter Client Co", names)
        self.assertNotIn("Status Filter Prospect Co", names)

    def test_search_companies_no_filter_returns_all(self):
        """Test that search_companies without filters returns every company."""
        service = self._get_company_service()
        service.create_company(SaveCompanyDTO(name="Company One"))
        service.create_company(SaveCompanyDTO(name="Company Two"))

        results = service.search_companies()

        self.assertIn("Company One", {c.name for c in results})
        self.assertIn("Company Two", {c.name for c in results})

    def test_stage_logo_stores_the_image_without_touching_a_company_row(self):
        """Test that stage_logo writes the image to the brick's file store and
        registers it as a ProjectFile, without requiring (or creating) a Company
        row - used to store a logo before a new company exists yet."""
        service = self._get_company_service()

        logo_file = service.stage_logo(_make_png_bytes(), "png")

        self.assertIsNotNone(ProjectFile.get_by_id(logo_file.id))
        path = logo_file.get_absolute_path()
        self.assertTrue(os.path.exists(path))
        with Image.open(path) as image:
            self.assertEqual(image.size, (2, 2))

    def test_stage_logo_refuses_a_file_that_is_not_an_image(self):
        """Test that stage_logo never stores bytes it cannot read as an image."""
        service = self._get_company_service()

        with self.assertRaises(BadRequestException):
            service.stage_logo(b"not-an-image", "png")

    def test_upload_logo_persists_the_file_on_existing_company(self):
        """Test that upload_logo stores the image in the file store and points the
        company at it immediately."""
        service = self._get_company_service()
        company = service.create_company(SaveCompanyDTO(name="Company With Logo"))

        updated = service.upload_logo(company.id, _make_png_bytes(color="blue"), "png")

        self.assertIsNotNone(updated.logo_file)
        self.assertTrue(os.path.exists(updated.logo_file.get_absolute_path()))

        # Persisted, not just returned in memory
        refetched = service.get_company(company.id)
        self.assertEqual(refetched.logo_file.id, updated.logo_file.id)

    def test_upload_logo_replaces_the_previous_one(self):
        """Test that replacing a logo deletes the file (and the row) it replaces:
        a company never keeps more than one logo in the store."""
        service = self._get_company_service()
        company = service.create_company(SaveCompanyDTO(name="Company Replacing Its Logo"))

        first = service.upload_logo(company.id, _make_png_bytes(), "png").logo_file
        first_id = first.id
        first_path = first.get_absolute_path()

        second = service.upload_logo(company.id, _make_png_bytes(color="blue"), "png").logo_file

        self.assertNotEqual(second.id, first_id)
        self.assertIsNone(ProjectFile.get_by_id(first_id))
        self.assertFalse(os.path.exists(first_path))
        self.assertTrue(os.path.exists(second.get_absolute_path()))

    def test_get_logo_data_url(self):
        """Test that the logo is served as an embeddable base64 data URL, the
        file store not being reachable over HTTP."""
        service = self._get_company_service()
        company = service.create_company(SaveCompanyDTO(name="Company With Logo Url"))

        self.assertIsNone(service.get_logo_data_url(company.id))

        service.upload_logo(company.id, _make_png_bytes(), "png")

        data_url = service.get_logo_data_url(company.id)
        self.assertTrue(data_url.startswith("data:image/png;base64,"))


# test_company_search_builder
class TestCompanySearchBuilder(BaseTestCase):
    """Test suite for CompanySearchBuilder, used directly (not through the service)."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_company_service(self) -> CompanyService:
        return CompanyService()

    def test_add_text_search_matches_name_case_insensitively(self):
        """Test that add_text_search performs a case-insensitive partial match on name."""
        service = self._get_company_service()
        service.create_company(SaveCompanyDTO(name="Constellab"))
        service.create_company(SaveCompanyDTO(name="Other Company"))

        search_builder = CompanySearchBuilder()
        search_builder.add_text_search("constella")
        results = search_builder.search_all()

        self.assertEqual({c.name for c in results}, {"Constellab"})

    def test_add_status_filter(self):
        """Test that add_status_filter only returns companies with that status.

        Scoped with distinctive names and assertIn/assertNotIn rather than exact
        set equality: tests in this suite share the same database (no per-test
        rollback), so other tests' companies with the same status may also be
        present in the results.
        """
        service = self._get_company_service()
        service.create_company(SaveCompanyDTO(name="Builder Prospect A", status=CompanyStatus.PROSPECT))
        service.create_company(SaveCompanyDTO(name="Builder Prospect B", status=CompanyStatus.PROSPECT))
        service.create_company(SaveCompanyDTO(name="Builder Client A", status=CompanyStatus.CLIENT))

        search_builder = CompanySearchBuilder()
        search_builder.add_status_filter(CompanyStatus.PROSPECT)
        results = search_builder.search_all()
        names = {c.name for c in results}

        self.assertIn("Builder Prospect A", names)
        self.assertIn("Builder Prospect B", names)
        self.assertNotIn("Builder Client A", names)

    def test_combined_text_and_status_filters(self):
        """Test chaining add_text_search and add_status_filter together."""
        service = self._get_company_service()
        service.create_company(SaveCompanyDTO(name="Acme Prospect", status=CompanyStatus.PROSPECT))
        service.create_company(SaveCompanyDTO(name="Acme Client", status=CompanyStatus.CLIENT))
        service.create_company(SaveCompanyDTO(name="Globex Prospect", status=CompanyStatus.PROSPECT))

        search_builder = CompanySearchBuilder()
        search_builder.add_text_search("Acme")
        search_builder.add_status_filter(CompanyStatus.PROSPECT)
        results = search_builder.search_all()

        self.assertEqual({c.name for c in results}, {"Acme Prospect"})

    def test_default_ordering_is_by_name(self):
        """Test that companies are returned ordered by name by default."""
        service = self._get_company_service()
        service.create_company(SaveCompanyDTO(name="Zebra Corp"))
        service.create_company(SaveCompanyDTO(name="Alpha Corp"))
        service.create_company(SaveCompanyDTO(name="Mango Corp"))

        search_builder = CompanySearchBuilder()
        results = search_builder.search_all()

        names = [c.name for c in results]
        self.assertEqual(names, sorted(names))


# test_company_logo_migration
class TestCompanyLogoMigration(BaseTestCase):
    """Test the data migration that moved the logos into the brick's file store."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def test_migrate_logos(self):
        """A logo stored the old way (an image in gws_core's rich text directory,
        its file name in a `logo_filename` column) is moved into the file store,
        attached to its company, and the directory it came from is removed."""
        service = CompanyService()
        company = service.create_company(SaveCompanyDTO(name="Legacy Logo Company"))

        db = ProjectDbManager.get_instance().db
        # Recreate the column the migration reads: it is gone from the model
        db.execute_sql(
            f"ALTER TABLE {Company.get_table_name()} ADD COLUMN {_OLD_LOGO_COLUMN} VARCHAR(255) NULL"
        )

        try:
            with Image.open(io.BytesIO(_make_png_bytes())) as image:
                saved = RichTextFileService.save_image(
                    _OLD_LOGO_OBJECT_TYPE, company.id, image, "png"
                )
            db.execute_sql(
                f"UPDATE {Company.get_table_name()} SET {_OLD_LOGO_COLUMN} = %s WHERE id = %s",
                (saved.filename, company.id),
            )

            Migration020Beta12._migrate_logos()

            migrated = Company.get_by_id_and_check(company.id)
            self.assertIsNotNone(migrated.logo_file)
            self.assertTrue(os.path.exists(migrated.logo_file.get_absolute_path()))
            self.assertEqual(migrated.logo_file.read_bytes(), _make_png_bytes())

            # the old storage is left empty behind it
            self.assertFalse(
                os.path.exists(
                    RichTextFileService.get_object_dir_path(_OLD_LOGO_OBJECT_TYPE, company.id)
                )
            )
        finally:
            db.execute_sql(
                f"ALTER TABLE {Company.get_table_name()} DROP COLUMN {_OLD_LOGO_COLUMN}"
            )

    def test_migrate_logos_with_a_missing_image(self):
        """A company whose image is no longer on disk is left without a logo,
        the migration must not fail on it."""
        service = CompanyService()
        company = service.create_company(SaveCompanyDTO(name="Lost Legacy Logo Company"))

        db = ProjectDbManager.get_instance().db
        db.execute_sql(
            f"ALTER TABLE {Company.get_table_name()} ADD COLUMN {_OLD_LOGO_COLUMN} VARCHAR(255) NULL"
        )

        try:
            db.execute_sql(
                f"UPDATE {Company.get_table_name()} SET {_OLD_LOGO_COLUMN} = %s WHERE id = %s",
                ("gone.png", company.id),
            )

            Migration020Beta12._migrate_logos()

            self.assertIsNone(Company.get_by_id_and_check(company.id).logo_file)
        finally:
            db.execute_sql(
                f"ALTER TABLE {Company.get_table_name()} DROP COLUMN {_OLD_LOGO_COLUMN}"
            )
