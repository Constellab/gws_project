import reflex as rx
from gws_project.company.company_dto import CompanyDTO
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_search_builder import ProjectSearchBuilder
from gws_reflex_main import ReflexMainState

from ..common.companies.company_page_state import CompanyPageState
from ..common.timestamp_text_component import format_timestamp


class CompanyDetailState(rx.State):
    """State for managing the company detail page.

    Handles fetching the details of a single company (from the URL) and the
    list of projects linked to it.
    """

    @rx.var
    async def company(self) -> CompanyDTO | None:
        """Return the current company DTO.

        :return: The current company DTO
        :rtype: Optional[CompanyDTO]
        """
        company_page_state = await self.get_state(CompanyPageState)
        current_company = await company_page_state.company()
        if current_company:
            return current_company.to_dto()
        return None

    @rx.var
    async def company_projects(self) -> list[ProjectDTO]:
        """Return the list of projects linked to the current company.

        :return: List of ProjectDTOs
        :rtype: list[ProjectDTO]
        """
        company = await self.company
        if not company:
            return []

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            search_builder = ProjectSearchBuilder()
            search_builder.add_company_filter(company.id)
            projects = search_builder.search_all()
            return [project.to_dto() for project in projects]

    @rx.var
    async def created_at_text(self) -> str:
        """Return the formatted creation timestamp of the current company."""
        company = await self.company
        return format_timestamp(company.created_at) if company else ""

    @rx.var
    async def last_modified_at_text(self) -> str:
        """Return the formatted last-modified timestamp of the current company."""
        company = await self.company
        return format_timestamp(company.last_modified_at) if company else ""
