from datetime import date, timedelta

import reflex as rx
from gws_core import UserDTO
from gws_core.space.space_service import SpaceService
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import TaskDTO, TaskStatus
from gws_project.task.task_search_builder import TaskSearchBuilder
from gws_project.task.task_service import TaskService
from gws_project.user.user import User
from gws_reflex_main import ReflexMainState

from ..common.breadcrumb.breadcrumb_state import Task
from ..common.kanban.kanban import BoardDataDTO, CardDTO, CardMoveEvent, build_kanban_board_data
from ..common.project_app_router import ProjectAppRouter


class KanbanState(rx.State):
    """State for managing the kanban board view of all tasks.

    This state handles fetching and displaying all tasks accessible to the user
    in a kanban board format, as well as managing task updates and deletion.
    """

    tasks: list[TaskDTO] = []
    _is_loaded: bool = False

    # Filter state
    search_text: str = ""
    selected_project_id: str = ""
    selected_user_id: str = ""
    selected_date_filter: str = "current_week"  # Default to current week

    # Data for filters
    available_projects: list[ProjectDTO] = []
    available_users: list[UserDTO] = []

    async def load_projects(self):
        """Load the list of projects for the current user."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            user_projects = ProjectService().get_current_user_projects()
            self.available_projects = [project.to_dto() for project in user_projects]

    async def load_users(self):
        """Load the list of all real users (excluding SYSUSER).

        The current user is placed first in the list.
        """
        main_state = await self.get_state(ReflexMainState)
        current_user = await main_state.get_and_check_current_user()
        users = User.get_real_users()

        # Convert to DTOs
        user_dtos = [user.to_dto() for user in users]

        # Move current user to the front
        current_user_dto = None
        other_users = []
        for user_dto in user_dtos:
            if user_dto.id == current_user.id:
                current_user_dto = user_dto
            else:
                other_users.append(user_dto)

        # Place current user first if found
        if current_user_dto:
            self.available_users = [current_user_dto] + other_users
        else:
            self.available_users = user_dtos

    def _get_date_range(self, filter_type: str) -> tuple[date | None, date | None]:
        """Calculate start and end dates based on the selected filter type.

        :param filter_type: One of 'all', 'current_week', 'next_week', 'current_month'
        :type filter_type: str
        :return: Tuple of (start_date, end_date), or (None, None) for 'all'
        :rtype: tuple[date | None, date | None]
        """
        if filter_type == "all":
            # No date filtering
            return None, None

        today = date.today()

        if filter_type == "current_week":
            # Get Monday of current week (weekday 0 = Monday)
            start_date = today - timedelta(days=today.weekday())
            # Get Sunday of current week
            end_date = start_date + timedelta(days=6)
        elif filter_type == "next_week":
            # Get Monday of next week
            start_date = today - timedelta(days=today.weekday()) + timedelta(weeks=1)
            # Get Sunday of next week
            end_date = start_date + timedelta(days=6)
        elif filter_type == "current_month":
            # First day of current month
            start_date = today.replace(day=1)
            # Last day of current month
            if today.month == 12:
                end_date = today.replace(day=31)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        else:
            # Default to current week
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

        return start_date, end_date

    async def load_tasks(self):
        """Fetch all tasks accessible to the current user with applied filters.

        Applies text search, project filter, user filter, and date filter using the TaskSearchBuilder.
        If no project filter is selected, returns tasks from all user's projects.

        :return: List of filtered tasks as DTOs
        :rtype: List[TaskDTO]
        """
        tasks: list[Task]

        # Build the search with filters
        search_builder = TaskSearchBuilder()

        # Project filter: if no specific project is selected, filter by all user projects
        if self.selected_project_id:
            search_builder.add_project_filter(self.selected_project_id)
        else:
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                user_projects = ProjectService().get_current_user_projects()
                project_ids = [project.id for project in user_projects]
                if project_ids:
                    search_builder.add_projects_filter(project_ids)
        # User/assignee filter
        if self.selected_user_id:
            search_builder.add_user_filter(self.selected_user_id)

        # Text search filter
        if self.search_text:
            search_builder.add_text_search(self.search_text)

        # Date filter - only applied if not 'all'
        start_date, end_date = self._get_date_range(self.selected_date_filter)
        if start_date is not None and end_date is not None:
            search_builder.add_date_range_filter(start_date, end_date)

        # only show the leaf tasks
        search_builder.add_allow_subtasks_filter(False)

        tasks = search_builder.search_all()

        self.tasks = [task.to_dto() for task in tasks]

    async def on_load(self):
        """Event handler called when the page loads.

        Loads projects, users, and tasks on page load.
        """
        await self.load_projects()
        await self.load_users()
        await self.load_tasks()

    async def handle_search_change(self, value: str):
        """Handle text search filter change.

        :param value: The search text
        :type value: str
        """
        self.search_text = value
        await self.load_tasks()

    async def handle_project_change(self, value: str):
        """Handle project filter change.

        :param value: The selected project ID (empty string for "All Projects")
        :type value: str
        """
        self.selected_project_id = value
        await self.load_tasks()

    async def handle_user_change(self, value: str):
        """Handle user/assignee filter change.

        :param value: The selected user ID (empty string for "All Users")
        :type value: str
        """
        self.selected_user_id = value
        await self.load_tasks()

    async def handle_date_filter_change(self, value: str):
        """Handle date filter change.

        :param value: The selected date filter ('current_week', 'next_week', 'current_month')
        :type value: str
        """
        self.selected_date_filter = value
        await self.load_tasks()

    async def clear_filters(self):
        """Clear all filters and reload tasks. Date filter is reset to current week."""
        self.search_text = ""
        self.selected_project_id = ""
        self.selected_user_id = ""
        self.selected_date_filter = "current_week"
        await self.load_tasks()

    @rx.var
    def project_options(self) -> list[tuple[str, str]]:
        """Get project options for select component (excluding the 'All Projects' option).

        :return: List of (id, title) tuples
        :rtype: List[tuple[str, str]]
        """
        return [(p.id, p.title) for p in self.available_projects]

    @rx.var
    def user_options(self) -> list[tuple[str, str]]:
        """Get user options for select component (excluding the 'All Users' option).

        :return: List of (id, full_name) tuples
        :rtype: List[tuple[str, str]]
        """
        return [(u.id, f"{u.first_name} {u.last_name}") for u in self.available_users]

    @rx.var
    async def kanban_board_data(self) -> BoardDataDTO:
        """Convert tasks to Kanban board format.

        :return: BoardDataDTO with columns structure for the Kanban board
        :rtype: BoardDataDTO
        """
        return build_kanban_board_data(self.tasks, self._task_to_card)

    def _task_to_card(self, task: TaskDTO) -> CardDTO:
        """Convert a TaskDTO to a Kanban card format."""
        assignee = task.assign_to.first_name + " " + task.assign_to.last_name if task.assign_to else "Unassigned"

        # Get assignee profile picture URL
        assignee_profile_picture_url = None
        if task.assign_to and task.assign_to.photo:
            assignee_profile_picture_url = SpaceService.get_user_profile_picture_url(task.assign_to.photo)

        # Get project name from project_id
        project_name = None
        if task.project_id:
            try:
                project = Project.get_by_id(task.project_id)
                project_name = project.title
            except Exception:
                pass

        return CardDTO(
            id=task.id,
            title=task.title,
            priority=task.priority.value,
            assignee=assignee,
            assignee_profile_picture_url=assignee_profile_picture_url,
            parent_task_title=task.parent_task_title,
            is_leaf=not task.allow_subtasks,
            project_name=project_name,
            start_date=task.start_date.isoformat() if task.start_date else None,
            end_date=task.end_date.isoformat() if task.end_date else None,
        )

    @rx.event(background=True)  # type: ignore
    async def handle_card_move(self, event_dict: dict):
        """Handle card movement in the Kanban board.

        :param event_dict: The event data containing card move information
        :type event_dict: dict
        """
        event = CardMoveEvent.from_json(event_dict)
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        try:
            # Extract task ID and new status from destination column
            task_id = event.card_id
            new_status_str = event.to_column_id

            if not task_id or not new_status_str:
                yield rx.toast.error("Invalid card move data")
                return

            # Convert status string to TaskStatus enum
            new_status = TaskStatus[new_status_str]

            # Update task status
            with await main_state.authenticate_user():
                task_service = TaskService()
                task = task_service.update_status(task_id, new_status)

                async with self:
                    await self._update_task(task)

        except Exception as e:
            yield rx.toast.error(f"Error moving task: {str(e)}")

    async def _update_task(self, task: Task):
        """Update a task in the state.

        :param task: The updated Task entity
        :type task: Task
        """
        if not self.tasks:
            return

        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task.to_dto()
                break

    async def handle_card_click(self, card_id: str):
        """Handle card click in the Kanban board.

        :param card_id: The ID of the clicked card
        :type card_id: str
        """
        # Navigate to task detail page
        return rx.redirect(ProjectAppRouter.get_task_detail_url(card_id))
