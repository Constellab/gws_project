import reflex as rx
from gws_core import UserDTO
from gws_project.task.task_dto import TaskDTO, TaskPriority, TaskStatus
from gws_project.task.task_service import TaskService
from gws_project.user.user import User
from gws_reflex_main import ConfirmDialogState, I18nState, ReflexMainState, toast_tr

from ..common.breadcrumb.breadcrumb_state import Task
from ..common.date_format import localize_task_dto
from ..common.projects.project_page_state import ProjectPageState, ProjectUrlParam
from ..common.tasks import (
    task_actions_translations,  # noqa: F401  (side effect: registers translations)
)
from ..move_task_dialog.move_task_dialog_state import MoveTaskDialogState
from ..task_form.task_form_dialog_state import TaskFormDialogState


class TaskListState(rx.State):
    """State for managing the task list within a project.

    This state handles fetching and displaying tasks for a specific project,
    as well as managing task deletion.
    """

    _url_params: ProjectUrlParam | None = None
    _tasks: list[Task] = []
    is_loading: bool = False

    # Filter state
    search_text: str = ""
    selected_status_filter: str = ""
    selected_priority_filter: str = ""
    selected_assignee_id: str = ""

    # Data for filters
    available_users: list[UserDTO] = []

    @rx.var
    async def current_object_id(self) -> str:
        """Get the current URL ID (project_id or task_id) to watch for changes.

        This var is used to detect URL changes and trigger task reloading.

        :return: Current URL ID
        :rtype: str
        """
        # Check for task_id_param first, then project_id_param
        project_state = await self.get_state(ProjectPageState)
        # url_param = await project_state.get_url_params()
        current_object = await project_state.get_object()

        if not current_object:
            return ""

        return current_object.id

    @rx.var
    async def get_tasks(self) -> list[TaskDTO]:
        """Return the list of tasks as DTOs, with the current filters applied.

        Tasks are loaded on component mount via fetch_tasks_on_mount event.
        Filtering happens in-memory since the full task list is already cached.

        :return: List of filtered TaskDTOs
        :rtype: List[TaskDTO]
        """
        lang = (await self.get_state(I18nState)).lang
        tasks = [localize_task_dto(task.to_dto(), lang) for task in self._tasks]

        if self.search_text:
            search_lower = self.search_text.lower()
            tasks = [task for task in tasks if search_lower in task.title.lower()]

        if self.selected_status_filter:
            status = TaskStatus(self.selected_status_filter)
            tasks = [task for task in tasks if task.status == status]

        if self.selected_priority_filter:
            priority = TaskPriority(self.selected_priority_filter)
            tasks = [task for task in tasks if task.priority == priority]

        if self.selected_assignee_id:
            tasks = [
                task
                for task in tasks
                if task.assign_to and task.assign_to.id == self.selected_assignee_id
            ]

        return tasks

    @rx.event(background=True)  # type: ignore
    async def fetch_tasks_on_mount(self):
        """Event handler to fetch tasks when the task list view is mounted.

        Checks if the current view mode is "list" and if the current URL params
        are the same as cached. If different, loads the tasks.
        """
        # Get current URL params and check if we need to fetch
        async with self:
            self._tasks = []  # Clear current tasks before loading new ones
            project_state = await self.get_state(ProjectPageState)
            url_param = await project_state.get_url_params()
            main_state = await self.get_state(ReflexMainState)

            if not url_param:
                return

            # Set loading state
            self._url_params = url_param
            self.is_loading = True

        # Fetch tasks outside of async with block
        try:
            with await main_state.authenticate_user():
                task_service = TaskService()

                if url_param.type == "project":
                    tasks = task_service.get_root_tasks_of_project(url_param.id)
                elif url_param.type == "task":
                    tasks = task_service.get_subtasks(url_param.id)
                else:
                    tasks = []

                users = User.get_real_users()

                async with self:
                    self._tasks = tasks
                    self.available_users = [user.to_dto() for user in users]
                    self.is_loading = False
        except Exception as e:
            async with self:
                self._tasks = []
                self.is_loading = False
            raise e

    @rx.event
    def handle_search_change(self, value: str):
        """Handle text search filter change.

        :param value: The search text
        :type value: str
        """
        self.search_text = value

    @rx.event
    def handle_status_filter_change(self, value: str):
        """Handle status filter change.

        :param value: The selected status ('BACKLOG', 'TODO', 'DOING', 'DONE', or '' for all)
        :type value: str
        """
        self.selected_status_filter = value

    @rx.event
    def handle_priority_filter_change(self, value: str):
        """Handle priority filter change.

        :param value: The selected priority ('HIGH', 'MEDIUM', 'LOW', or '' for all)
        :type value: str
        """
        self.selected_priority_filter = value

    @rx.event
    def handle_assignee_change(self, value: str):
        """Handle assignee filter change.

        :param value: The selected user ID (empty string for "All Assignees")
        :type value: str
        """
        self.selected_assignee_id = value

    @rx.event
    def clear_filters(self):
        """Clear all task filters."""
        self.search_text = ""
        self.selected_status_filter = ""
        self.selected_priority_filter = ""
        self.selected_assignee_id = ""

    async def add_or_update_task(self, task: Task):
        """Update a task in the state.

        :param updated_task: The updated TaskDTO
        :type updated_task: TaskDTO
        """
        if self._tasks is None:
            return

        updated = False
        for i, task_ in enumerate(self._tasks):
            if task_.id == task.id:
                self._tasks[i] = task
                updated = True
                break

        if not updated:
            self._tasks.append(task)

        # Refresh current object because sub task might affect parent task data
        project_state = await self.get_state(ProjectPageState)
        await project_state.refresh_object()

    async def open_update_task_dialog(self, task_id: str):
        """Open the update task dialog.

        :param task_id: The ID of the task to update
        :type task_id: str
        """
        # Find the task in the local list
        task = None
        for t in self._tasks:
            if t.id == task_id:
                task = t
                break

        if not task:
            yield await toast_tr.error(self, "task_actions.toast.not_found")
            return

        form_state = await self.get_state(TaskFormDialogState)

        await form_state.open_update_dialog(task=task, callback_after_close=self.add_or_update_task)

    @rx.event
    async def open_move_task_dialog(self, task: TaskDTO):
        """Open the move task dialog for the given task.

        :param task: The task to move
        :type task: TaskDTO
        """
        move_dialog_state = await self.get_state(MoveTaskDialogState)
        await move_dialog_state.open_move_dialog(
            task=task, callback_after_close=self._on_task_moved
        )

    async def _on_task_moved(self, task: Task):
        """Callback invoked after a task is moved.

        Keeps the local list in sync with the move: if the task still belongs in the
        current view (same project root list, or same parent task's subtask list), it's
        refreshed in place; otherwise it's removed since it now lives elsewhere.

        :param task: The moved task
        :type task: Task
        """
        still_here = False
        if self._url_params:
            if self._url_params.type == "project":
                still_here = task.project.id == self._url_params.id and task.parent_task is None
            elif self._url_params.type == "task":
                still_here = bool(task.parent_task) and task.parent_task.id == self._url_params.id

        if still_here:
            await self.add_or_update_task(task)
        else:
            await self.delete_task(task.id)

    @rx.event
    async def open_change_task_type_dialog(self, task: TaskDTO):
        """Open a confirmation dialog to change the task type (allow_subtasks).

        :param task: The task to change the type of
        :type task: TaskDTO
        """
        confirm_dialog_state = await self.get_state(ConfirmDialogState)
        i18n = await self.get_state(I18nState)

        if task.allow_subtasks:
            confirm_dialog_state.open_dialog(
                title=i18n.tr("task_actions.convert_to_leaf.title"),
                content=i18n.tr("task_actions.convert_to_leaf.content"),
                action=lambda: self._change_task_type_action(task.id, False),
            )
        else:
            confirm_dialog_state.open_dialog(
                title=i18n.tr("task_actions.convert_to_parent.title"),
                content=i18n.tr("task_actions.convert_to_parent.content"),
                action=lambda: self._change_task_type_action(task.id, True),
            )

    async def _change_task_type_action(self, task_id: str, allow_subtasks: bool):
        """Action to change the task type after confirmation."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            updated_task = task_service.update_allow_subtasks(task_id, allow_subtasks)

        yield await toast_tr.success(self, "task_actions.toast.type_changed")

        await self.add_or_update_task(updated_task)

    @rx.event
    async def open_delete_task_dialog(self, task: TaskDTO):
        """Open the delete task confirmation dialog.

        :param task: The task to delete
        :type task: TaskDTO
        """
        delete_dialog_state = await self.get_state(ConfirmDialogState)
        i18n = await self.get_state(I18nState)

        # Build confirmation message
        content = i18n.tr("task_actions.delete.content")
        if task.allow_subtasks:
            content += " " + i18n.tr("task_actions.delete.descendants_warning")

        delete_dialog_state.open_dialog(
            title=i18n.tr("task_actions.delete.title"),
            content=content,
            action=lambda: self._delete_action(task.id),
        )

    async def _delete_action(self, task_id: str):
        """Delete the task from the list."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            task_service.delete_task(task_id)

        # Show success toast
        yield await toast_tr.success(self, "task_actions.toast.deleted")

        # Remove from list
        await self.delete_task(task_id)

    async def delete_task(self, task_id: str):
        """Delete a task and its subtasks from the state.

        :param task_id: The ID of the task to delete
        :type task_id: str
        """
        if self._tasks:
            self._tasks = [task for task in self._tasks if task.id != task_id]

        # Refresh current object because sub task might affect parent task data
        project_state = await self.get_state(ProjectPageState)
        await project_state.refresh_object()

    def clear_state(self):
        """Clear the state when leaving the page."""
        self._tasks = []
        self._url_params = None
        self.is_loading = False
        self.search_text = ""
        self.selected_status_filter = ""
        self.selected_priority_filter = ""
        self.selected_assignee_id = ""
