import io
from typing import ClassVar

from gws_core import BadRequestException, CurrentUserService
from PIL import Image

from gws_project.company.company import Company
from gws_project.company.company_dto import CompanyStatus, SaveCompanyDTO
from gws_project.company.company_search_builder import CompanySearchBuilder
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.document.project_file import ProjectFile
from gws_project.document.project_file_service import ProjectFileService
from gws_project.user.app_role_service import AppRoleService
from gws_project.user.user_app_role import AppRole

# Name the logo is stored under in the file store. The store de-duplicates it, so
# every company keeps its own node.
LOGO_FILE_BASE_NAME = "company_logo"


class CompanyService:
    """Service class for managing companies.

    Companies are shared, global entities (not scoped to a project's membership) and
    can never be deleted - there is intentionally no delete_company method.

    Reading is open to any authenticated user of the app; creating and modifying a
    company (including its logo) requires one of the `COMPANY_WRITE_ROLES` app roles.
    """

    # App roles allowed to create or modify a company. Companies are shared reference
    # data, so writing them is gated on the app-level role rather than on the membership
    # of any single project. MEMBER being the default role, this currently accepts every
    # real user of the app; it is the single place to narrow that down.
    COMPANY_WRITE_ROLES: ClassVar[list[AppRole]] = [AppRole.ADMIN, AppRole.MEMBER]

    def _check_can_write(self) -> None:
        """Check the current user's app role allows creating/modifying a company.

        :raises UnauthorizedException: If the current user holds none of the
            `COMPANY_WRITE_ROLES` app roles
        """
        current_user = CurrentUserService.get_and_check_current_user()

        AppRoleService.check_has_one_of_roles(
            current_user.id, self.COMPANY_WRITE_ROLES, "create or modify a company"
        )

    def get_company(self, company_id: str) -> Company:
        """Get a company by ID.

        :param company_id: The ID of the company to retrieve
        :type company_id: str
        :return: The company
        :rtype: Company
        :raises NotFoundException: If the company is not found
        """
        return Company.get_by_id_and_check(company_id)

    def search_companies(
        self, search_text: str | None = None, status: CompanyStatus | None = None
    ) -> list[Company]:
        """Search companies with optional text and status filters.

        :param search_text: Text to search in the company name
        :type search_text: str | None
        :param status: Status to filter by
        :type status: CompanyStatus | None
        :return: List of matching companies
        :rtype: list[Company]
        """
        search_builder = CompanySearchBuilder()

        if search_text:
            search_builder.add_text_search(search_text)

        if status:
            search_builder.add_status_filter(status)

        return search_builder.search_all()

    @ProjectDbManager.transaction()
    def create_company(self, company_dto: SaveCompanyDTO) -> Company:
        """Create a company.

        :param company_dto: The company data to create. Its `logo_file_id`, if set,
            must reference a ProjectFile staged beforehand via `stage_logo` (the
            "New Company" dialog lets the user pick a logo before the company exists).
        :type company_dto: SaveCompanyDTO
        :return: The created company
        :rtype: Company
        :raises UnauthorizedException: If the current user's app role does not allow it
        :raises BadRequestException: If `logo_file_id` references no stored file
        """
        self._check_can_write()

        company = Company()
        company.name = company_dto.name
        company.address = company_dto.address
        company.siren = company_dto.siren
        company.phone = company_dto.phone
        company.status = company_dto.status
        company.logo_file = self._get_staged_logo_file(company_dto.logo_file_id)
        company.save()

        return company

    @ProjectDbManager.transaction()
    def update_company(self, company_id: str, company_dto: SaveCompanyDTO) -> Company:
        """Update a company.

        :param company_id: The ID of the company to update
        :type company_id: str
        :param company_dto: The updated company data
        :type company_dto: SaveCompanyDTO
        :return: The updated company
        :rtype: Company
        :raises UnauthorizedException: If the current user's app role does not allow it
        """
        self._check_can_write()

        company = Company.get_by_id_and_check(company_id)

        company.name = company_dto.name
        company.address = company_dto.address
        company.siren = company_dto.siren
        company.phone = company_dto.phone
        company.status = company_dto.status
        company.save()

        return company

    def get_logo_data_url(self, company_id: str) -> str | None:
        """Return the logo of a company as a base64 ``data:`` URL, ready for an <img>.

        The file store is not served over HTTP, so the image is embedded in the page
        instead of being linked. Reading a logo is open to any authenticated user,
        like reading the company itself.

        :param company_id: The ID of the company
        :type company_id: str
        :return: The data URL, or None if the company has no logo (or its file is gone)
        :rtype: str | None
        :raises NotFoundException: If the company is not found
        """
        company = Company.get_by_id_and_check(company_id)

        if company.logo_file is None:
            return None

        return company.logo_file.to_data_url()

    def stage_logo(self, image_bytes: bytes, extension: str) -> ProjectFile:
        """Store a logo image without attaching it to any company.

        Used by the "New Company" dialog: the user can pick a logo before the company
        exists, and `create_company` is then called with the returned file's id. A
        dialog the user abandons leaves the file unreferenced in the store.

        :param image_bytes: The raw bytes of the uploaded image
        :type image_bytes: bytes
        :param extension: The image file extension (e.g. "png", "jpg")
        :type extension: str
        :return: The ProjectFile registering the stored image
        :rtype: ProjectFile
        :raises UnauthorizedException: If the current user's app role does not allow it
        :raises BadRequestException: If the bytes are not a readable image
        """
        self._check_can_write()

        # Refuse anything that is not an image before it reaches the store: the
        # accepted types of the upload field are only a client-side hint.
        try:
            with Image.open(io.BytesIO(image_bytes)):
                pass
        except Exception as exception:
            raise BadRequestException("The uploaded file is not an image") from exception

        return ProjectFileService.create_from_bytes(
            image_bytes, f"{LOGO_FILE_BASE_NAME}.{extension}"
        )

    def upload_logo(self, company_id: str, image_bytes: bytes, extension: str) -> Company:
        """Upload/replace the logo of an existing company.

        The bytes are stored in the brick's dedicated LocalFileStore, exactly like a
        project document, and the company references the resulting ProjectFile. The
        logo it replaces is deleted, so a company never keeps more than one file.

        :param company_id: The ID of the company
        :type company_id: str
        :param image_bytes: The raw bytes of the uploaded image
        :type image_bytes: bytes
        :param extension: The image file extension (e.g. "png", "jpg")
        :type extension: str
        :return: The updated company
        :rtype: Company
        :raises UnauthorizedException: If the current user's app role does not allow it
        """
        # stage_logo runs the same check, but keep it explicit here too: the check must
        # not depend on which helper this method happens to delegate the storage to.
        self._check_can_write()

        company = Company.get_by_id_and_check(company_id)
        logo_file = self.stage_logo(image_bytes, extension)

        previous_logo_file = self._attach_logo(company, logo_file)

        # Deleting the bytes is not transactional: it happens once the row pointing at
        # them is committed, never before.
        if previous_logo_file is not None:
            previous_logo_file.delete_file_from_store()

        return company

    @ProjectDbManager.transaction()
    def _attach_logo(self, company: Company, logo_file: ProjectFile) -> ProjectFile | None:
        """Point a company at a new logo file and drop the row of the previous one.

        :param company: The company to update
        :type company: Company
        :param logo_file: The ProjectFile of the new logo
        :type logo_file: ProjectFile
        :return: The ProjectFile of the replaced logo, whose bytes the caller must
            delete after the transaction, or None if the company had no logo
        :rtype: ProjectFile | None
        """
        previous_logo_file: ProjectFile | None = company.logo_file

        company.logo_file = logo_file
        company.save()

        if previous_logo_file is not None:
            previous_logo_file.delete_instance()

        return previous_logo_file

    def _get_staged_logo_file(self, logo_file_id: str | None) -> ProjectFile | None:
        """Resolve the ProjectFile a logo was staged under, if any.

        :param logo_file_id: The id returned by `stage_logo`, or None
        :type logo_file_id: str | None
        :return: The ProjectFile, or None if no logo was staged
        :rtype: ProjectFile | None
        :raises BadRequestException: If the id references no stored file
        """
        if not logo_file_id:
            return None

        logo_file: ProjectFile | None = ProjectFile.get_by_id(logo_file_id)
        if logo_file is None:
            raise BadRequestException("The logo of this company was not stored, upload it again.")

        return logo_file
