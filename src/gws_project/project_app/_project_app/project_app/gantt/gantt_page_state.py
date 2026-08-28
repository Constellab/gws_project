import reflex as rx
from gws_core import UserDTO
from gws_project.company.company_dto import CompanyDTO
from gws_project.company.company_service import CompanyService
from gws_project.project.project_dto import ProjectWithRootTasksDTO
from gws_project.project.project_service import ProjectService
from gws_project.user.user import User
from gws_reflex_main import ReflexMainState

from ..common.details_sidebar.details_panel_state import DetailsPanelState
from ..common.gantt.gantt_type import GanttDataDTO, GanttStatus
from ..common.gantt.gantt_utils import build_gantt_data_from_projects


class GanttPageState(rx.State):
    """State for the portfolio Gantt view.

    Loads every project the user can see with its root tasks, applies the toolbar filters
    server-side, and exposes the ready-to-draw payload plus the header counters.
    """

    projects_with_tasks: list[ProjectWithRootTasksDTO] = []
    view_mode: str = "Week"

    # Filter state
    search_title: str = ""
    selected_manager_id: str = ""
    selected_company_id: str = ""
    show_completed: bool = False

    # Bumped by the "Today" button; the chart re-centres whenever this changes.
    recenter_token: int = 0

    # Data for manager/company filters
    available_managers: list[UserDTO] = []
    available_companies: list[CompanyDTO] = []

    async def load_managers(self):
        """Load the list of all users who can be project managers."""
        users = User.get_real_users()
        self.available_managers = [user.to_dto() for user in users]

    async def load_companies(self):
        """Load the list of all companies for the company filter."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            companies = CompanyService().search_companies()
            self.available_companies = [company.to_dto() for company in companies]

    async def load_projects_with_tasks(self):
        """Load all projects with their root tasks for the current user, with filters."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            project_service = ProjectService()
            self.projects_with_tasks = project_service.search_current_user_projects_with_root_tasks(
                search_title=self.search_title,
                manager_id=self.selected_manager_id,
                company_id=self.selected_company_id,
            )

    async def on_load(self):
        """Event handler called when the page loads.

        Loads managers, companies, and projects with tasks on page load.
        """
        await self.load_managers()
        await self.load_companies()
        await self.load_projects_with_tasks()

    async def handle_project_click(self, project_id: str):
        """Show the clicked project in the details panel.

        :param project_id: The clicked project id
        :type project_id: str
        """
        details_panel = await self.get_state(DetailsPanelState)
        await details_panel.open_project(
            project_id, callback_after_change=self.load_projects_with_tasks
        )

    async def handle_task_click(self, task_id: str):
        """Show the clicked task in the details panel.

        The chart is reloaded after an edit: a task's status colours its row and feeds
        its project's own status, progress and group.

        :param task_id: The clicked task id
        :type task_id: str
        """
        details_panel = await self.get_state(DetailsPanelState)
        await details_panel.open_task(
            task_id, callback_after_change=self.load_projects_with_tasks
        )

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
    async def handle_company_change(self, value: str):
        """Handle company filter change."""
        self.selected_company_id = value
        await self.load_projects_with_tasks()

    @rx.event
    def handle_show_completed_change(self, value: bool):
        """Show or hide the "Terminé" group.

        Purely a display concern: the projects are already loaded, so this does not re-query.

        :param value: Whether finished projects should be shown
        :type value: bool
        """
        self.show_completed = value

    @rx.event
    async def clear_filters(self):
        """Clear all filters and reload projects."""
        self.search_title = ""
        self.selected_manager_id = ""
        self.selected_company_id = ""
        await self.load_projects_with_tasks()

    @rx.event
    def recenter_on_today(self):
        """Re-centre the timeline on today."""
        self.recenter_token += 1

    @rx.event
    def handle_view_mode_change(self, value: str | list[str]):
        """Handle zoom change.

        :param value: The new zoom level ('Day', 'Week', 'Month', 'Year')
        :type value: str | list[str]
        """
        if isinstance(value, list):
            self.view_mode = value[0] if value else "Week"
        else:
            self.view_mode = value

    @rx.var
    def company_options(self) -> list[tuple[str, str]]:
        """Get company options for select component.

        :return: List of (id, name) tuples
        :rtype: list[tuple[str, str]]
        """
        return [(c.id, c.name) for c in self.available_companies]

    @rx.var
    def gantt_data(self) -> GanttDataDTO:
        """Convert the loaded projects into the chart payload.

        :return: The Gantt payload
        :rtype: GanttDataDTO
        """
        return build_gantt_data_from_projects(self.projects_with_tasks)

    @rx.var
    def visible_projects(self) -> list[ProjectWithRootTasksDTO]:
        """Projects actually drawn, i.e. minus the finished ones when they are hidden.

        The header counters must match what the chart shows, so they are derived from the
        same rule the chart applies rather than from the raw result set.

        :return: The visible projects
        :rtype: list[ProjectWithRootTasksDTO]
        """
        if self.show_completed:
            return self.projects_with_tasks
        # Match on id: projects missing a start or due date are absent from the payload
        # entirely, so the two lists are not positionally aligned.
        done_ids = {
            project.id for project in self.gantt_data.projects if project.status == GanttStatus.DONE
        }
        return [item for item in self.projects_with_tasks if item.project.id not in done_ids]

    @rx.var
    def project_count(self) -> int:
        """Number of projects currently drawn.

        :return: Project count
        :rtype: int
        """
        return len(self.visible_projects)

    @rx.var
    def manager_count(self) -> int:
        """Number of distinct project managers across the drawn projects.

        :return: Manager count
        :rtype: int
        """
        return len({
            item.project.project_manager.id
            for item in self.visible_projects
            if item.project.project_manager is not None
        })
