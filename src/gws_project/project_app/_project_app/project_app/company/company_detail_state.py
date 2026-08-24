import reflex as rx
from gws_project.company.company_dto import CompanyDTO
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_reflex_main import I18nState, ReflexMainState

from ..common.companies.company_page_state import CompanyPageState
from ..common.date_format import localize_project_dto
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
        """Return the projects of the current company the user is a member of.

        Scoped through ProjectService: a company groups the projects of several
        teams, and this page must not expose the ones the user has no access to.

        :return: List of ProjectDTOs
        :rtype: list[ProjectDTO]
        """
        company = await self.company
        if not company:
            return []

        main_state = await self.get_state(ReflexMainState)
        lang = (await self.get_state(I18nState)).lang
        with await main_state.authenticate_user():
            projects = ProjectService().search_current_user_projects(
                company_id=company.id
            )
            return [localize_project_dto(project.to_dto(), lang) for project in projects]

    @rx.var
    async def created_at_text(self) -> str:
        """Return the formatted creation timestamp of the current company."""
        company = await self.company
        if not company:
            return ""
        lang = (await self.get_state(I18nState)).lang
        return format_timestamp(company.created_at, lang)

    @rx.var
    async def last_modified_at_text(self) -> str:
        """Return the formatted last-modified timestamp of the current company."""
        company = await self.company
        if not company:
            return ""
        lang = (await self.get_state(I18nState)).lang
        return format_timestamp(company.last_modified_at, lang)
