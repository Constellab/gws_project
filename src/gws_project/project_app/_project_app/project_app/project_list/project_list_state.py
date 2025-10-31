from typing import List

import reflex as rx
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_reflex_main import ReflexMainState

from ..common.project_app_router import ProjectAppRouter


class ProjectListState(ReflexMainState):
    """State for managing the project list page.

    This state handles fetching and displaying the list of projects
    for the current user.
    """

    projects: List[ProjectDTO] = []
    is_loading: bool = False
    error_message: str = ""

    async def load_projects(self):
        """Load the list of projects for the current user.

        This method fetches all projects that the current user is a member of
        and converts them to DTOs for display in the frontend.
        """
        # Check authentication before accessing data
        if not await self.check_authentication():
            self.error_message = "You must be authenticated to view projects"
            return

        self.is_loading = True
        self.error_message = ""

        try:

            projects: List[Project]
            with await self.authenticate_user():
                project_service = ProjectService()
                projects = project_service.get_current_user_projects()

            # Convert projects to DTOs
            self.projects = [project.to_dto() for project in projects]

        finally:
            self.is_loading = False

    async def on_load(self):
        """Event handler called when the page loads.

        This method is automatically called by Reflex when the page is loaded.
        """
        await self.load_projects()

    @rx.event
    def open_create_dialog(self):
        """Open the create project dialog."""
        from ..project_form_dialog.project_form_dialog_state import \
            ProjectFormDialogState

        ProjectFormDialogState.open_dialog(on_close=self.load_projects)

    @rx.event
    def go_to_project(self, project_id: str):
        """Navigate to the project detail page for the given project ID.

        :param project_id: The ID of the project to navigate to
        :type project_id: str
        """
        return rx.redirect(ProjectAppRouter.get_project_detail_url(project_id))
