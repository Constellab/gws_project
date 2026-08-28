from datetime import date, timedelta

import reflex as rx
from gws_core import UserDTO
from gws_core.space.space_service import SpaceService
from gws_project.company.company_dto import CompanyDTO
from gws_project.company.company_service import CompanyService
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import TaskDTO, TaskStatus
from gws_project.task.task_service import TaskService
from gws_project.user.user import User
from gws_reflex_main import I18nState, ReflexMainState, toast_tr

from ..common.breadcrumb.breadcrumb_state import Task
from ..common.date_format import localize_task_dto
from ..common.details_sidebar.details_panel_state import DetailsPanelState
from ..common.kanban.kanban import BoardDataDTO, CardDTO, CardMoveEvent, build_kanban_board_data


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
    selected_company_id: str = ""
    selected_date_filter: str = "current_week"  # Default to current week
    # Backlog tasks are hidden by default to avoid cluttering the board with a column
    # most users don't need to see; the user can opt in via the "Show Backlog" toggle.
    show_backlog: bool = False

    # Data for filters
    available_projects: list[ProjectDTO] = []
    available_users: list[UserDTO] = []
    available_companies: list[CompanyDTO] = []

    async def load_projects(self):
        """Load the list of projects for the current user."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            user_projects = ProjectService().get_current_user_projects()
            self.available_projects = [project.to_dto() for project in user_projects]

    async def load_companies(self):
        """Load the list of all companies for the company filter."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            companies = CompanyService().search_companies()
            self.available_companies = [company.to_dto() for company in companies]

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

        :param filter_type: One of 'all', 'last_week', 'current_week', 'next_week', 'current_month'
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
        elif filter_type == "last_week":
            # Get Monday of last week
            start_date = today - timedelta(days=today.weekday()) - timedelta(weeks=1)
            # Get Sunday of last week
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
        """Fetch the tasks accessible to the current user with the applied filters.

        Every filter is passed to TaskService, which owns the authorization: the
        selected project id comes from the frontend, so it must never reach a search
        query without its role being checked first. With no project selected, the
        service bounds the search to the projects the user is a member of.
        """
        # Date filter - only applied if not 'all'
        start_date, end_date = self._get_date_range(self.selected_date_filter)

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            tasks = TaskService().search_current_user_tasks(
                project_id=self.selected_project_id or None,
                company_id=self.selected_company_id or None,
                assigned_user_id=self.selected_user_id or None,
                search_text=self.search_text or None,
                start_date=start_date,
                end_date=end_date,
                # only show the leaf tasks
                allow_subtasks=False,
                # Backlog tasks are excluded unless the user opted in via the "Show Backlog" toggle
                exclude_statuses=None if self.show_backlog else [TaskStatus.BACKLOG],
            )

            lang = (await self.get_state(I18nState)).lang
            self.tasks = [localize_task_dto(task.to_dto(), lang) for task in tasks]

    async def on_load(self):
        """Event handler called when the page loads.

        Loads projects, users, companies, and tasks on page load.
        """
        await self.load_projects()
        await self.load_users()
        await self.load_companies()
        await self.load_tasks()

    async def handle_card_click(self, card_id: str):
        """Show the clicked card's task in the details panel.

        The board is reloaded after an edit: a status change moves the card to another
        column, which only a reload can draw.

        :param card_id: The id of the clicked card, i.e. of its task
        :type card_id: str
        """
        details_panel = await self.get_state(DetailsPanelState)
        await details_panel.open_task(card_id, callback_after_change=self.load_tasks)

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

    async def handle_company_change(self, value: str):
        """Handle company filter change.

        :param value: The selected company ID (empty string for "All Companies")
        :type value: str
        """
        self.selected_company_id = value
        await self.load_tasks()

    async def handle_date_filter_change(self, value: str):
        """Handle date filter change.

        :param value: The selected date filter ('last_week', 'current_week', 'next_week', 'current_month')
        :type value: str
        """
        self.selected_date_filter = value
        await self.load_tasks()

    async def handle_show_backlog_change(self, value: bool):
        """Handle the "Show Backlog" toggle change.

        :param value: Whether the Backlog column should be shown
        :type value: bool
        """
        self.show_backlog = value
        await self.load_tasks()

    async def clear_filters(self):
        """Clear all filters and reload tasks. Date filter is reset to current week."""
        self.search_text = ""
        self.selected_project_id = ""
        self.selected_user_id = ""
        self.selected_company_id = ""
        self.selected_date_filter = "current_week"
        self.show_backlog = False
        await self.load_tasks()

    @rx.var
    def project_options(self) -> list[tuple[str, str]]:
        """Get project options for select component (excluding the 'All Projects' option).

        :return: List of (id, title) tuples
        :rtype: List[tuple[str, str]]
        """
        return [(p.id, p.title) for p in self.available_projects]

    @rx.var
    def company_options(self) -> list[tuple[str, str]]:
        """Get company options for select component (excluding the 'All Companies' option).

        :return: List of (id, name) tuples
        :rtype: List[tuple[str, str]]
        """
        return [(c.id, c.name) for c in self.available_companies]

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
        i18n = await self.get_state(I18nState)
        column_titles = {
            TaskStatus.BACKLOG.value: i18n.tr("kanban_board.column.backlog"),
            TaskStatus.TODO.value: i18n.tr("kanban_board.column.todo"),
            TaskStatus.DOING.value: i18n.tr("kanban_board.column.doing"),
            TaskStatus.DONE.value: i18n.tr("kanban_board.column.done"),
        }
        return build_kanban_board_data(
            self.tasks,
            lambda task: self._task_to_card(task, i18n),
            include_backlog=self.show_backlog,
            column_titles=column_titles,
        )

    def _task_to_card(self, task: TaskDTO, i18n: I18nState) -> CardDTO:
        """Convert a TaskDTO to a Kanban card format."""
        assignee = (
            task.assign_to.first_name + " " + task.assign_to.last_name
            if task.assign_to
            else i18n.tr("kanban_board.card.unassigned")
        )

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
            due_date=task.due_date.isoformat() if task.due_date else None,
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
                yield await toast_tr.error(self, "kanban.toast.invalid_move")
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
            yield await toast_tr.error(
                self, "kanban.toast.move_failed", {"error": str(e)}
            )

    async def _update_task(self, task: Task):
        """Update a task in the state.

        :param task: The updated Task entity
        :type task: Task
        """
        if not self.tasks:
            return

        lang = (await self.get_state(I18nState)).lang
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = localize_task_dto(task.to_dto(), lang)
                break

    async def add_task(self, task: Task):
        """Add a newly created task to the board (used by the quick-add row).

        :param task: The newly created Task entity
        :type task: Task
        """
        lang = (await self.get_state(I18nState)).lang
        self.tasks = self.tasks + [localize_task_dto(task.to_dto(), lang)]

