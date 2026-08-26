from gws_core import (
    NullableCharField,
    NullableForeignKeyField,
    TypedCharField,
    TypedEnumField,
)

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.document.project_file import ProjectFile

from ..core.model_with_user import ModelWithUser
from .company_dto import CompanyDTO, CompanyStatus


class Company(ModelWithUser):
    """
    Company model - Represents a company that can optionally be linked to projects.

    A company can never be deleted (no delete method/route exists for it).

    The logo is stored like every other file of the brick: the bytes live in the
    dedicated ``LocalFileStore`` and this row only references the ``ProjectFile``
    that registers them (see ``ProjectFileService``). The store is not served over
    HTTP, so the app embeds the image as a data URL (``CompanyService.get_logo_data_url``).
    """

    name = TypedCharField(max_length=255)
    address = NullableCharField(max_length=500)
    siren = NullableCharField(max_length=9)
    phone = NullableCharField(max_length=30)
    logo_file = NullableForeignKeyField(ProjectFile, backref="+")
    status = TypedEnumField(choices=CompanyStatus, max_length=20, default=CompanyStatus.PROSPECT.value)

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
            # The image itself is NOT part of the DTO: companies are listed and
            # searched everywhere, and embedding a base64 logo in every row would
            # be paid on every list. Only the pages that display it ask for it.
            has_logo=self.logo_file is not None,
        )

    class Meta:
        table_name = "gws_project_companies"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
