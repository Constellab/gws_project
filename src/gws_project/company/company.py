import os

from gws_core import NullableCharField, TypedCharField, TypedEnumField

from gws_project.core.project_db_manager import ProjectDbManager

from ..core.model_with_user import ModelWithUser
from .company_dto import CompanyDTO, CompanyStatus

# Object type used to namespace this company's logo files in gws_core's generic
# RichTextFileService storage (shared with note images, scoped by object_type/object_id).
COMPANY_LOGO_OBJECT_TYPE = "company_logo"


def build_company_logo_url(company_id: str, logo_filename: str) -> str:
    """Build the publicly readable URL of a company logo file.

    Standalone helper (rather than only a Company method) so a logo staged for a
    not-yet-created company (see CompanyService.stage_logo) can also be previewed
    before the Company row exists.

    :param company_id: The id the logo was stored under (the company's id, or the
        pending id generated client-side before a new company is created)
    :type company_id: str
    :param logo_filename: The stored logo filename
    :type logo_filename: str
    :return: The logo URL
    :rtype: str
    """
    lab_api_url = os.environ["GWS_LAB_API_URL"].rstrip("/")
    return f"{lab_api_url}/core-api/rich-text/{COMPANY_LOGO_OBJECT_TYPE}/{company_id}/image/{logo_filename}"


class Company(ModelWithUser):
    """
    Company model - Represents a company that can optionally be linked to projects.

    A company can never be deleted (no delete method/route exists for it).
    """

    name = TypedCharField(max_length=255)
    address = NullableCharField(max_length=500)
    siren = NullableCharField(max_length=9)
    phone = NullableCharField(max_length=30)
    logo_filename = NullableCharField(max_length=255)
    status = TypedEnumField(choices=CompanyStatus, max_length=20, default=CompanyStatus.PROSPECT.value)

    def get_logo_url(self) -> str | None:
        """Build the publicly readable URL of the company logo, if any.

        Reuses gws_core's generic rich-text image serving route instead of a
        dedicated endpoint (see RichTextFileService.save_image / upload_image).

        :return: The logo URL, or None if no logo was uploaded
        :rtype: str | None
        """
        if not self.logo_filename:
            return None

        return build_company_logo_url(self.id, self.logo_filename)

    def to_dto(self) -> CompanyDTO:
        return CompanyDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            address=self.address,
            siren=self.siren,
            phone=self.phone,
            status=self.status,
            logo_url=self.get_logo_url(),
        )

    class Meta:
        table_name = "gws_project_companies"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
