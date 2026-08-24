import reflex as rx
from gws_project.company.company_dto import CompanyDTO, CompanyStatus
from gws_project.company.company_service import CompanyService
from gws_reflex_main import ReflexMainState

from ..common.company_app_router import CompanyAppRouter


class CompanyListState(rx.State):
    """State for managing the company list page.

    Handles fetching and displaying the list of companies with filtering
    capabilities (text search, status).
    """

    companies: list[CompanyDTO] = []
    is_loading: bool = False

    # Filter state
    search_text: str = ""
    selected_status_filter: str = ""

    async def load_companies(self):
        """Load the list of companies with the currently applied filters."""
        main_state = await self.get_state(ReflexMainState)
        if not await main_state.check_authentication():
            return

        self.is_loading = True
        try:
            # Through the service rather than a search builder built here: the app
            # never queries the database directly, so authorization always applies.
            with await main_state.authenticate_user():
                self.companies = [
                    company.to_dto()
                    for company in CompanyService().search_companies(
                        search_text=self.search_text or None,
                        status=CompanyStatus(self.selected_status_filter)
                        if self.selected_status_filter
                        else None,
                    )
                ]
        finally:
            self.is_loading = False

    async def on_load(self):
        """Event handler called when the page loads."""
        await self.load_companies()

    @rx.event
    async def handle_search_change(self, value: str):
        """Handle text search filter change."""
        self.search_text = value
        await self.load_companies()

    @rx.event
    async def handle_status_filter_change(self, value: str):
        """Handle status filter change (empty string for "All statuses")."""
        self.selected_status_filter = value
        await self.load_companies()

    @rx.event
    async def clear_filters(self):
        """Clear all filters and reload companies."""
        self.search_text = ""
        self.selected_status_filter = ""
        await self.load_companies()

    @rx.event
    def go_to_company(self, company_id: str):
        """Navigate to the company detail page for the given company ID."""
        return rx.redirect(CompanyAppRouter.get_company_detail_url(company_id))
