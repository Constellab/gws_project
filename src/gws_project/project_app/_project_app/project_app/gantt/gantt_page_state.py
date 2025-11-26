import reflex as rx
from gws_core import UserDTO
from gws_project.project.project_dto import ProjectWithRootTasksDTO
from gws_project.project.project_service import ProjectService
from gws_project.user.user import User
from gws_reflex_main import ReflexMainState

from ..common.gantt.gantt_type import GanttDataDTO
from ..common.gantt.gantt_utils import build_gantt_data_from_projects
from ..common.project_app_router import ProjectAppRouter


class GanttPageState(ReflexMainState):
    """State for managing the gantt chart view of all projects and their root tasks.

    This state handles fetching and displaying all projects with their root tasks
    in a Gantt chart format, as well as managing navigation to task details.
    """

    projects_with_tasks: list[ProjectWithRootTasksDTO] = []
    view_mode: str = "Week"

    # Filter state
    search_title: str = ""
    selected_manager_id: str = ""

    # Data for manager filter
    available_managers: list[UserDTO] = []

    async def load_managers(self):
        """Load the list of all users who can be project managers."""
        users = User.get_real_users()
        self.available_managers = [user.to_dto() for user in users]

    async def load_projects_with_tasks(self):
        """Load all projects with their root tasks for the current user, with filters."""
        with await self.authenticate_user():
            project_service = ProjectService()
            self.projects_with_tasks = project_service.search_current_user_projects_with_root_tasks(
                search_title=self.search_title,
                manager_id=self.selected_manager_id,
            )

    async def on_load(self):
        """Event handler called when the page loads.

        Loads managers and projects with tasks on page load.
        """
        await self.load_managers()
        await self.load_projects_with_tasks()

    @rx.event
    async def handle_search_title_change(self, value: str):
        """Handle project title filter change."""
        self.search_title = value
        await self.load_projects_with_tasks()

    @rx.event
    async def handle_manager_change(self, value: str):
        """Handle manager filter change."""
        self.selected_manager_id = value
        await self.load_projects_with_tasks()

    @rx.event
    async def clear_filters(self):
        """Clear all filters and reload projects."""
        self.search_title = ""
        self.selected_manager_id = ""
        await self.load_projects_with_tasks()

    @rx.var
    def gantt_data(self) -> GanttDataDTO:
        """Convert projects with tasks to Gantt chart format.

        :return: GanttDataDTO for the Gantt chart
        :rtype: GanttDataDTO
        """
        return build_gantt_data_from_projects(self.projects_with_tasks)

    async def handle_task_click(self, task_id: str):
        """Handle task click in the Gantt chart.

        :param task_id: The ID of the clicked task
        :type task_id: str
        """
        # Check if this is a project (starts with "project-") or a task
        if task_id.startswith("project-"):
            # Extract project ID and navigate to project detail
            project_id = task_id.replace("project-", "")
            return rx.redirect(f"/project/{project_id}")
        else:
            # Navigate to task detail page
            return rx.redirect(ProjectAppRouter.get_task_detail_url(task_id))

    @rx.event
    async def handle_view_mode_change(self, value: str | list[str]):
        """Handle view mode change in the Gantt chart.

        :param value: The new view mode ('Day', 'Week', 'Month', 'Year')
        :type value: str
        """
        if isinstance(value, list):
            self.view_mode = value[0] if value else "Month"
        else:
            self.view_mode = value
