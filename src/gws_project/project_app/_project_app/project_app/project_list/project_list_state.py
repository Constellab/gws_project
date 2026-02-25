import reflex as rx
from gws_core import UserDTO
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

    # Data for filters
    available_managers: list[UserDTO] = []

    def _compute_project_count(self):
        """Compute project count statistics from the loaded projects list."""
        ongoing = 0
        done = 0
        todo = 0
        for project in self.projects:
            if project.status == ProjectStatus.COMPLETED:
                done += 1
            elif project.status == ProjectStatus.ACTIVE:
                ongoing += 1
            else:
                todo += 1

        self.project_count = ProjectCountDTO(
            total=len(self.projects),
            ongoing=ongoing,
            done=done,
            todo=todo,
        )

    async def load_managers(self):
        """Load the list of all users who can be project managers.

        Loads all real users (excluding SYSUSER) sorted by name.
        """
        users = User.get_real_users()
        self.available_managers = [user.to_dto() for user in users]

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

            projects = search_builder.search_all()

            # Convert projects to DTOs
            self.projects = [project.to_dto() for project in projects]

            # Compute project count from loaded projects
            self._compute_project_count()

        finally:
            self.is_loading = False

    async def on_load(self):
        """Event handler called when the page loads.

        This method is automatically called by Reflex when the page is loaded.
        """
        await self.load_managers()
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
    async def clear_filters(self):
        """Clear all filters and reload projects."""
        self.search_text = ""
        self.selected_manager_id = ""
        await self.load_projects()

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
