import reflex as rx
from gws_core import UserDTO
from gws_project.company.company_dto import CompanyDTO
from gws_project.company.company_service import CompanyService
from gws_project.project.project_count_dto import ProjectCountDTO
from gws_project.project.project_dto import ProjectDTO, ProjectStatus
from gws_project.project.project_search_builder import ProjectSearchBuilder
from gws_project.user.user import User
from gws_reflex_main import ReflexMainState

from ..common.project_app_router import ProjectAppRouter


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

        Uses ProjectSearchBuilder to apply text search and project manager filters.
        """
        # Check authentication before accessing data
        main_state = await self.get_state(ReflexMainState)
        if not await main_state.check_authentication():
            self.error_message = "You must be authenticated to view projects"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            current_user = await main_state.get_and_check_current_user()

            # Build the search with filters
            search_builder = ProjectSearchBuilder()

            # Filter by user's projects (projects where user is a member)
            search_builder.add_project_user_filter(current_user.id)

            # Text search filter
            if self.search_text:
                search_builder.add_text_search(self.search_text)

            # Project manager filter
            if self.selected_manager_id:
                search_builder.add_project_manager_filter(self.selected_manager_id)

            # Company filter
            if self.selected_company_id:
                search_builder.add_company_filter(self.selected_company_id)

            projects = search_builder.search_all()

            # Convert projects to DTOs
            self._all_projects = [project.to_dto() for project in projects]

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
