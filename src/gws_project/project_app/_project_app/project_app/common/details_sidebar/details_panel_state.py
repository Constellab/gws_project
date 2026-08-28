"""State of the details panel: the task/project sidebar opened from a list, board or chart."""

from collections.abc import Awaitable, Callable

import reflex as rx
from gws_core import UserDTO
from gws_project.project.project_dto import ProjectDTO, ProjectUserDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import TaskDTO, TaskPriority, TaskStatus
from gws_project.task.task_service import TaskService
from gws_reflex_main import I18nState, ReflexMainState, toast_tr

from ..date_format import localize_project_dto, localize_task_dto
from ..project_app_router import ProjectAppRouter
from ..tasks import (
    task_actions_translations,  # noqa: F401  (side effect: registers translations)
)
from ..timestamp_text_component import format_timestamp

# Called after the panel changed what it is showing, so the screen behind it can reload
# its own copy of the data (the board's columns, the week's slots, the timeline's rows).
PanelChangeCallback = Callable[[], Awaitable[None]]


class DetailsPanelState(rx.State):
    """The task or project details panel shared by Kanban, Gantt, Planning and My work.

    Those screens list work that lives elsewhere: clicking a row used to leave the screen
    for the detail page, losing the board, the week or the timeline the user was reading.
    The panel shows the same sidebar the detail page shows, next to the screen it was
    opened from, and its "Open this task"/"Open this project" button is what navigates.

    A task's status and priority are editable here, exactly as they are on the detail
    page. The screen behind the panel holds its own copy of the task, so it has to be
    told: the state that opens the panel passes the reload to run afterwards, and
    `open_task`/`open_project` are therefore called from that state rather than bound
    straight to a click in the frontend.
    """

    # Whether the panel is showing, and what it is showing ("" | "task" | "project").
    is_open: bool = False
    kind: str = ""

    # Task payload
    task: TaskDTO | None = None
    # The task's project. The detail page leaves it to the breadcrumb; the panel opens
    # over cross-project screens, where "which project is this?" is the first question.
    task_project: ProjectDTO | None = None
    parent_task: TaskDTO | None = None
    subtask_members: list[UserDTO] = []

    # Project payload
    project: ProjectDTO | None = None
    project_users: list[ProjectUserDTO] = []

    # Shared metadata, pre-formatted in the session's language
    created_at_text: str = ""
    last_modified_at_text: str = ""

    # Reload of the screen the panel was opened from, run after an edit.
    _callback_after_change: PanelChangeCallback | None = None

    async def open_task(
        self, task_id: str, callback_after_change: PanelChangeCallback | None = None
    ):
        """Show a task in the panel.

        A missing task, or one belonging to a project the user has left, raises out of the
        service and is turned into a toast by the app's global handler.

        :param task_id: The id of the task to show
        :type task_id: str
        :param callback_after_change: Reload of the calling screen, run after the panel
            edits the task (optional)
        :type callback_after_change: PanelChangeCallback | None
        """
        self._clear()
        self._callback_after_change = callback_after_change
        await self._load_task(task_id)
        self.kind = "task"
        self.is_open = True

    async def open_project(
        self, project_id: str, callback_after_change: PanelChangeCallback | None = None
    ):
        """Show a project in the panel.

        :param project_id: The id of the project to show
        :type project_id: str
        :param callback_after_change: Reload of the calling screen, run after the panel
            edits the project (optional)
        :type callback_after_change: PanelChangeCallback | None
        """
        main_state = await self.get_state(ReflexMainState)
        lang = (await self.get_state(I18nState)).lang

        with await main_state.authenticate_user():
            project_service = ProjectService()
            project = project_service.get_project(project_id)
            project_users = project_service.get_project_users(project_id)

        self._clear()
        self._callback_after_change = callback_after_change
        self.project = localize_project_dto(project.to_dto(), lang)
        self.project_users = [project_user.to_dto() for project_user in project_users]
        self.created_at_text = format_timestamp(self.project.created_at, lang)
        self.last_modified_at_text = format_timestamp(self.project.last_modified_at, lang)
        self.kind = "project"
        self.is_open = True

    async def update_status(self, new_status: str):
        """Change the shown task's status, then refresh the panel and its screen.

        :param new_status: The new status name
        :type new_status: str
        """
        if not self.task:
            yield await toast_tr.error(self, "task_actions.toast.not_found")
            return

        task_id = self.task.id
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            TaskService().update_status(task_id, TaskStatus[new_status])

        await self._after_task_change(task_id)

    async def update_priority(self, new_priority: str):
        """Change the shown task's priority, then refresh the panel and its screen.

        :param new_priority: The new priority name
        :type new_priority: str
        """
        if not self.task:
            yield await toast_tr.error(self, "task_actions.toast.not_found")
            return

        task_id = self.task.id
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            TaskService().update_priority(task_id, TaskPriority[new_priority])

        await self._after_task_change(task_id)

    @rx.event
    def set_is_open(self, value: bool):
        """Follow the panel's own open state (Escape, click outside, drag down).

        :param value: The new open state
        :type value: bool
        """
        self.is_open = value

    @rx.event
    def close(self):
        """Close the panel, keeping its content so the closing animation has something
        to draw."""
        self.is_open = False

    @rx.var
    def detail_url(self) -> str:
        """The detail page of whatever the panel is showing.

        A var rather than a redirect from an event handler: the "Open this" control is a
        real link, so the router can fetch that page's code while the panel is being read
        instead of only once the click happens. The detail pages carry the rich-text
        editor, which is by far the heaviest route of the app to load.

        :return: The detail page URL, or "" when the panel shows nothing
        :rtype: str
        """
        if self.kind == "task" and self.task:
            return ProjectAppRouter.get_task_detail_url(self.task.id)
        if self.kind == "project" and self.project:
            return ProjectAppRouter.get_project_detail_url(self.project.id)
        return ""

    async def _load_task(self, task_id: str) -> None:
        """Read a task and fill the panel's task payload with it.

        :param task_id: The id of the task to read
        :type task_id: str
        """
        main_state = await self.get_state(ReflexMainState)
        lang = (await self.get_state(I18nState)).lang

        with await main_state.authenticate_user():
            task_service = TaskService()
            task = task_service.get_task(task_id)
            members = (
                task_service.get_descendants_assigned_users(task_id)
                if task.allow_subtasks
                else []
            )

        self.task = localize_task_dto(task.to_dto(), lang)
        self.task_project = localize_project_dto(task.project.to_dto(), lang)
        self.parent_task = (
            localize_task_dto(task.parent_task.to_dto(), lang) if task.parent_task else None
        )
        self.subtask_members = [member.to_dto() for member in members]
        self.created_at_text = format_timestamp(self.task.created_at, lang)
        self.last_modified_at_text = format_timestamp(self.task.last_modified_at, lang)

    async def _after_task_change(self, task_id: str) -> None:
        """Re-read the edited task, then let the screen behind the panel reload.

        The task is re-read rather than patched in place: a status change also moves the
        progress, and an ancestor's own status and progress are recomputed from it.

        :param task_id: The id of the task that changed
        :type task_id: str
        """
        await self._load_task(task_id)

        if self._callback_after_change:
            await self._callback_after_change()

    def _clear(self) -> None:
        """Drop the previous content, so a task panel never shows a leftover project
        section (and the other way round)."""
        self.task = None
        self.task_project = None
        self.parent_task = None
        self.subtask_members = []
        self.project = None
        self.project_users = []
        self.created_at_text = ""
        self.last_modified_at_text = ""
        self._callback_after_change = None
