import reflex as rx
from gws_project.task.task_dto import TaskDTO
from gws_project.task.task_service import TaskService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.breadcrumb.breadcrumb_state import Task
from ..common.projects.project_page_state import ProjectPageState, ProjectUrlParam
from ..task_form.task_form_dialog_state import TaskFormDialogState


class TaskListState(ReflexMainState):
    """State for managing the task list within a project.

    This state handles fetching and displaying tasks for a specific project,
    as well as managing task deletion.
    """

    _url_params: ProjectUrlParam | None = None
    _tasks: list[Task] = []
    is_loading: bool = False

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
        """Return the list of tasks as DTOs.

        Tasks are loaded on component mount via fetch_tasks_on_mount event.

        :return: List of TaskDTOs
        :rtype: List[TaskDTO]
        """
        return [task.to_dto() for task in self._tasks]

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

            if not url_param:
                return

            # Set loading state
            self._url_params = url_param
            self.is_loading = True

        # Fetch tasks outside of async with block
        try:
            with await self.authenticate_user():
                task_service = TaskService()

                if url_param.type == "project":
                    tasks = task_service.get_root_tasks_of_project(url_param.id)
                elif url_param.type == "task":
                    tasks = task_service.get_subtasks(url_param.id)
                else:
                    tasks = []

                async with self:
                    self._tasks = tasks
                    self.is_loading = False
        except Exception as e:
            async with self:
                self._tasks = []
                self.is_loading = False
            raise e

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
            yield rx.toast.error("Task not found")
            return

        form_state = await self.get_state(TaskFormDialogState)

        await form_state.open_update_dialog(task=task, callback_after_close=self.add_or_update_task)

    @rx.event
    async def open_change_task_type_dialog(self, task: TaskDTO):
        """Open a confirmation dialog to change the task type (allow_subtasks).

        :param task: The task to change the type of
        :type task: TaskDTO
        """
        confirm_dialog_state = await self.get_state(ConfirmDialogState)

        if task.allow_subtasks:
            confirm_dialog_state.open_dialog(
                title="Convert to normal task",
                content="Are you sure you want to convert this task to a normal task? "
                "Status, priority, dates and progress will become manually managed.",
                action=lambda: self._change_task_type_action(task.id, False),
            )
        else:
            confirm_dialog_state.open_dialog(
                title="Convert to task with subtasks",
                content="Are you sure you want to convert this task to a task with subtasks? "
                "Status, priority, dates and progress will be automatically calculated from subtasks.",
                action=lambda: self._change_task_type_action(task.id, True),
            )

    async def _change_task_type_action(self, task_id: str, allow_subtasks: bool):
        """Action to change the task type after confirmation."""
        with await self.authenticate_user():
            task_service = TaskService()
            updated_task = task_service.update_allow_subtasks(task_id, allow_subtasks)

        yield rx.toast.success("Task type changed successfully")

        await self.add_or_update_task(updated_task)

    @rx.event
    async def open_delete_task_dialog(self, task: TaskDTO):
        """Open the delete task confirmation dialog.

        :param task: The task to delete
        :type task: TaskDTO
        """
        delete_dialog_state = await self.get_state(ConfirmDialogState)

        # Build confirmation message
        warning = ""
        if task.allow_subtasks:
            warning = " This will also delete all its descendants (subtasks, sub-subtasks, etc.)."

        delete_dialog_state.open_dialog(
            title="Delete Task",
            content=f"Are you sure you want to delete this task?{warning}",
            action=lambda: self._delete_action(task.id),
        )

    async def _delete_action(self, task_id: str):
        """Delete the task from the list."""
        with await self.authenticate_user():
            task_service = TaskService()
            task_service.delete_task(task_id)

        # Show success toast
        yield rx.toast.success("Task deleted successfully")

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
