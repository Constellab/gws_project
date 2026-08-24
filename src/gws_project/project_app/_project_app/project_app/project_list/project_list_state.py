import reflex as rx
from gws_core import UserDTO
from gws_project.company.company_dto import CompanyDTO
from gws_project.company.company_service import CompanyService
from gws_project.project.project_count_dto import ProjectCountDTO
from gws_project.project.project_dto import ProjectDTO, ProjectStatus
from gws_project.project.project_service import ProjectService
from gws_project.user.user import User
from gws_reflex_main import I18nState, ReflexMainState

from ..common.date_format import localize_project_dto
from ..common.project_app_router import ProjectAppRouter
from . import project_list_translations  # noqa: F401  (side effect: registers translations)


class ProjectListState(rx.State):
    """State for managing the project list page.

    This state handles fetching and displaying the list of projects
    for the current user with filtering capabilities.
    """

    projects: list[ProjectDTO] = []
    project_count: ProjectCountDTO = ProjectCountDTO(total=0, ongoing=0, done=0, todo=0)
    is_loading: bool = False
    error_message: str = ""

    # Filter state
    search_text: str = ""
    selected_manager_id: str = ""
    selected_company_id: str = ""
    selected_status_filter: str = ""

    # Data for filters
    available_managers: list[UserDTO] = []
    available_companies: list[CompanyDTO] = []

    # All projects matching the text/manager filters, before the status filter is applied.
    # Kept separate so the stat cards always reflect the full counts, regardless of which
    # status card is currently selected.
    _all_projects: list[ProjectDTO] = []

    def _compute_project_count(self):
        """Compute project count statistics from the full (status-unfiltered) projects list."""
        ongoing = 0
        done = 0
        todo = 0
        for project in self._all_projects:
            if project.status == ProjectStatus.COMPLETED:
                done += 1
            elif project.status == ProjectStatus.ACTIVE:
                ongoing += 1
            else:
                todo += 1

        self.project_count = ProjectCountDTO(
            total=len(self._all_projects),
            ongoing=ongoing,
            done=done,
            todo=todo,
        )

    def _apply_status_filter(self) -> list[ProjectDTO]:
        """Filter `_all_projects` by `selected_status_filter`, since project status is
        computed on the fly and can't be filtered at the database level.

        :return: The projects matching the currently selected status filter
        :rtype: list[ProjectDTO]
        """
        if not self.selected_status_filter:
            return self._all_projects

        status = ProjectStatus(self.selected_status_filter)
        return [project for project in self._all_projects if project.status == status]

    async def load_managers(self):
        """Load the list of all users who can be project managers.

        Loads all real users (excluding SYSUSER) sorted by name.
        """
        users = User.get_real_users()
        self.available_managers = [user.to_dto() for user in users]

    async def load_companies(self):
        """Load the list of all companies for the company filter."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            companies = CompanyService().search_companies()
            self.available_companies = [company.to_dto() for company in companies]

    async def load_projects(self):
        """Load the list of projects for the current user with applied filters.

        The search itself is delegated to ProjectService, which owns the membership
        filter: the manager and company ids come from the frontend, so they must not
        reach a search query that is not already bounded to the user's projects.
        """
        # Check authentication before accessing data
        main_state = await self.get_state(ReflexMainState)
        i18n = await self.get_state(I18nState)
        if not await main_state.check_authentication():
            self.error_message = i18n.tr("project_list.error.not_authenticated")
            return

        self.is_loading = True
        self.error_message = ""

        try:
            with await main_state.authenticate_user():
                projects = ProjectService().search_current_user_projects(
                    search_title=self.search_text or None,
                    manager_id=self.selected_manager_id or None,
                    company_id=self.selected_company_id or None,
                )

            # Convert projects to DTOs, with their dates in the active language
            self._all_projects = [
                localize_project_dto(project.to_dto(), i18n.lang) for project in projects
            ]

            # Compute project count from the full (status-unfiltered) list
            self._compute_project_count()

            # Apply the status filter (if any) for display
            self.projects = self._apply_status_filter()

        finally:
            self.is_loading = False

    async def on_load(self):
        """Event handler called when the page loads.

        This method is automatically called by Reflex when the page is loaded.
        """
        await self.load_managers()
        await self.load_companies()
        await self.load_projects()

    @rx.event
    async def handle_search_change(self, value: str):
        """Handle text search filter change.

        :param value: The search text
        :type value: str
        """
        self.search_text = value
        await self.load_projects()

    @rx.event
    async def handle_manager_change(self, value: str):
        """Handle project manager filter change.

        :param value: The selected manager user ID (empty string for "All Managers")
        :type value: str
        """
        self.selected_manager_id = value
        await self.load_projects()

    @rx.event
    async def handle_company_change(self, value: str):
        """Handle company filter change.

        :param value: The selected company ID (empty string for "All Companies")
        :type value: str
        """
        self.selected_company_id = value
        await self.load_projects()

    @rx.event
    async def clear_filters(self):
        """Clear all filters and reload projects."""
        self.search_text = ""
        self.selected_manager_id = ""
        self.selected_company_id = ""
        self.selected_status_filter = ""
        await self.load_projects()

    @rx.event
    def handle_status_filter_click(self, status: str):
        """Handle a click on one of the stat cards (Ongoing, Completed, Not started).

        Clicking the already-selected card clears the filter (toggle behavior).

        :param status: The `ProjectStatus` value to filter by (e.g. "ACTIVE")
        :type status: str
        """
        self.selected_status_filter = "" if self.selected_status_filter == status else status
        self.projects = self._apply_status_filter()

    @rx.event
    def open_create_dialog(self):
        """Open the create project dialog."""
        from ..project_form_dialog.project_form_dialog_state import ProjectFormDialogState

        ProjectFormDialogState.open_dialog(on_close=self.load_projects)

    @rx.event
    def go_to_project(self, project_id: str):
        """Navigate to the project detail page for the given project ID.

        :param project_id: The ID of the project to navigate to
        :type project_id: str
        """
        return rx.redirect(ProjectAppRouter.get_project_detail_url(project_id))
