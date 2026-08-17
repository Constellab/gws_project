import io
import os
from unittest.mock import patch

from gws_core import BaseTestCase, CurrentUserService, NotFoundException, RichTextFileService
from gws_project.company.company import COMPANY_LOGO_OBJECT_TYPE, Company
from gws_project.company.company_dto import CompanyStatus, SaveCompanyDTO
from gws_project.company.company_search_builder import CompanySearchBuilder
from gws_project.company.company_service import CompanyService
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
        self.assertIsNone(company.logo_filename)
        self.assertEqual(company.created_by.id, current_user.id)
        self.assertEqual(company.last_modified_by.id, current_user.id)

        # Companies have no logo yet, so to_dto() must not need GWS_LAB_API_URL
        dto = company.to_dto()
        self.assertEqual(dto.name, "Full Company")
        self.assertEqual(dto.status, CompanyStatus.CLIENT)
        self.assertIsNone(dto.logo_url)

    def test_create_company_name_only(self):
        """Test that every field except name is optional and defaults sensibly."""
        service = self._get_company_service()

        company = service.create_company(SaveCompanyDTO(name="Minimal Company"))

        self.assertEqual(company.name, "Minimal Company")
        self.assertIsNone(company.address)
        self.assertIsNone(company.siren)
        self.assertIsNone(company.phone)
        self.assertIsNone(company.logo_filename)
        self.assertEqual(company.status, CompanyStatus.PROSPECT)

    def test_create_company_with_forced_id(self):
        """Test that create_company honors an explicit company_id (used to match a
        logo already staged under a client-generated pending id)."""
        service = self._get_company_service()
        forced_id = "11111111-2222-3333-4444-555555555555"

        company = service.create_company(SaveCompanyDTO(name="Pending Id Company"), company_id=forced_id)

        self.assertEqual(company.id, forced_id)
        self.assertEqual(Company.get_by_id_and_check(forced_id).name, "Pending Id Company")

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

    def test_stage_logo_writes_file_without_touching_a_company_row(self):
        """Test that stage_logo writes the image to disk under the given id,
        without requiring (or creating) a Company row - used to stage a logo
        before a new company exists yet."""
        service = self._get_company_service()
        pending_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

        filename = service.stage_logo(pending_id, _make_png_bytes(), "png")

        path = RichTextFileService.get_object_file_path(COMPANY_LOGO_OBJECT_TYPE, pending_id, filename)
        self.assertTrue(os.path.exists(path))
        with Image.open(path) as image:
            self.assertEqual(image.size, (2, 2))

    def test_upload_logo_persists_filename_on_existing_company(self):
        """Test that upload_logo stores the image and updates the company's
        logo_filename immediately."""
        service = self._get_company_service()
        company = service.create_company(SaveCompanyDTO(name="Company With Logo"))

        updated = service.upload_logo(company.id, _make_png_bytes(color="blue"), "png")

        self.assertIsNotNone(updated.logo_filename)
        path = RichTextFileService.get_object_file_path(
            COMPANY_LOGO_OBJECT_TYPE, company.id, updated.logo_filename
        )
        self.assertTrue(os.path.exists(path))

        # Persisted, not just returned in memory
        refetched = service.get_company(company.id)
        self.assertEqual(refetched.logo_filename, updated.logo_filename)

    def test_get_logo_url_with_logo(self):
        """Test that Company.get_logo_url builds the expected rich-text image URL
        once a logo has been uploaded."""
        service = self._get_company_service()
        company = service.create_company(SaveCompanyDTO(name="Company With Logo Url"))
        updated = service.upload_logo(company.id, _make_png_bytes(), "png")

        with patch.dict(os.environ, {"GWS_LAB_API_URL": "https://test-lab.example.com"}):
            url = updated.get_logo_url()

        self.assertEqual(
            url,
            f"https://test-lab.example.com/core-api/rich-text/{COMPANY_LOGO_OBJECT_TYPE}"
            f"/{updated.id}/image/{updated.logo_filename}",
        )


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
