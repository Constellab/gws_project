import io
from typing import ClassVar

from gws_core import CurrentUserService, RichTextFileService
from PIL import Image

from gws_project.company.company import COMPANY_LOGO_OBJECT_TYPE, Company
from gws_project.company.company_dto import CompanyStatus, SaveCompanyDTO
from gws_project.company.company_search_builder import CompanySearchBuilder
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.user.app_role_service import AppRoleService
from gws_project.user.user_app_role import AppRole


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
    def create_company(self, company_dto: SaveCompanyDTO, company_id: str | None = None) -> Company:
        """Create a company.

        :param company_dto: The company data to create. Its `logo_filename`, if
            set, must have been staged beforehand via `stage_logo` under `company_id`
            (the "New Company" dialog lets the user pick a logo before the company
            exists yet, using a client-generated pending id).
        :type company_dto: SaveCompanyDTO
        :param company_id: Id to force on the created row, matching the pending id
            a logo may already have been staged under (optional)
        :type company_id: str | None
        :return: The created company
        :rtype: Company
        :raises UnauthorizedException: If the current user's app role does not allow it
        """
        self._check_can_write()

        company = Company()
        if company_id:
            company.id = company_id
        company.name = company_dto.name
        company.address = company_dto.address
        company.siren = company_dto.siren
        company.phone = company_dto.phone
        company.status = company_dto.status
        company.logo_filename = company_dto.logo_filename
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

    def stage_logo(self, object_id: str, image_bytes: bytes, extension: str) -> str:
        """Save a logo image to disk without touching any Company row.

        Used by the "New Company" dialog: the user can pick a logo before the
        company is created, using a client-generated pending id as `object_id`.
        `create_company` is later called with that same id, so the staged file
        ends up under the company's final id without ever being moved.

        :param object_id: The id to store the image under (the company's id, or a
            not-yet-created company's pending id)
        :type object_id: str
        :param image_bytes: The raw bytes of the uploaded image
        :type image_bytes: bytes
        :param extension: The image file extension (e.g. "png", "jpg")
        :type extension: str
        :return: The stored filename
        :rtype: str
        :raises UnauthorizedException: If the current user's app role does not allow it
        """
        self._check_can_write()

        image = Image.open(io.BytesIO(image_bytes))
        result = RichTextFileService.save_image(COMPANY_LOGO_OBJECT_TYPE, object_id, image, extension)
        return result.filename

    @ProjectDbManager.transaction()
    def upload_logo(self, company_id: str, image_bytes: bytes, extension: str) -> Company:
        """Upload/replace the logo of an existing company.

        Reuses gws_core's generic RichTextFileService image storage (the same
        mechanism used for note images) instead of a dedicated file store, so no
        new HTTP endpoint is needed to serve it back.

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

        company.logo_filename = self.stage_logo(company_id, image_bytes, extension)
        company.save()

        return company
