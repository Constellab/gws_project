from enum import Enum

from gws_core import BaseModelDTO, ModelDTO, UserDTO


class CompanyStatus(Enum):
    """Status of a company"""

    PARTENAIRE = "PARTENAIRE"
    PROSPECT = "PROSPECT"
    CLIENT = "CLIENT"


class SaveCompanyDTO(BaseModelDTO):
    name: str
    address: str | None = None
    siren: str | None = None
    phone: str | None = None
    status: CompanyStatus = CompanyStatus.PROSPECT
    # Filename of a logo staged via CompanyService.stage_logo before the company
    # existed (create flow only - ignored by update_company).
    logo_filename: str | None = None


class CompanyDTO(ModelDTO):
    """DTO for displaying company information in the frontend."""

    name: str
    address: str | None
    siren: str | None
    phone: str | None
    status: CompanyStatus
    logo_url: str | None
    created_by: UserDTO
    last_modified_by: UserDTO
