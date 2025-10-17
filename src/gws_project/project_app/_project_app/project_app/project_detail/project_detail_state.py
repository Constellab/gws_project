from typing import Optional

from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_reflex_main import ReflexMainState


class ProjectDetailState(ReflexMainState):
    """State for managing the project detail page.

    This state handles fetching and displaying the details of a single project
    based on the project ID from the URL.
    """

    project: Optional[ProjectDTO] = None
    is_loading: bool = False
    error_message: str = ""
    _project_id: str = ""

    async def load_project(self, project_id: str):
        """Load the project details based on the project ID.

        :param project_id: The ID of the project to load
        :type project_id: str
        """
        # Check authentication before accessing data
        if not await self.check_authentication():
            self.error_message = "You must be authenticated to view project details"
            return

        self.is_loading = True
        self.error_message = ""
        self._project_id = project_id

        try:
            project: Optional[Project]
            with await self.authenticate_user():
                project_service = ProjectService()
                project = project_service.get_project(project_id)
                self.project = project.to_dto()

        except Exception as e:
            self.error_message = f"Error loading project: {str(e)}"
            self.project = None

        finally:
            self.is_loading = False

    async def on_load(self):
        """Event handler called when the page loads.

        This method is automatically called by Reflex when the page is loaded.
        It extracts the project_id from the URL and loads the project.
        """
        # Get project_id from the router
        project_id = self.project_id
        if project_id:
            await self.load_project(project_id)
        else:
            self.error_message = "No project ID provided"
