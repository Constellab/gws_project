from typing import List, Optional

import reflex as rx
from gws_project.task.task_dto import TaskDTO
from gws_project.task.task_service import TaskService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.breadcrumb.breadcrumb_state import Task
from ..common.project_page_state import ProjectPageState, ProjectUrlParam
from ..task_form.task_form_dialog_state import TaskFormDialogState


class TaskListState(ReflexMainState):
    """State for managing the task list within a project.

    This state handles fetching and displaying tasks for a specific project,
    as well as managing task deletion.
    """

    _url_params: Optional[ProjectUrlParam] = None
    _tasks: List[Task] = []
    is_loading: bool = False

    @rx.var
    async def get_tasks(self) -> List[TaskDTO]:
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

            project_state = await self.get_state(ProjectPageState)
            url_param = await project_state.get_url_params()

            if not url_param:
                return

            # Check if we already have tasks for this URL param
            previous_id = self._url_params.id if self._url_params else None
            current_id = url_param.id if url_param else None

            if previous_id == current_id and len(self._tasks) > 0:
                return  # Already loaded for this URL param

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

        for i, task_ in enumerate(self._tasks):
            if task_.id == task.id:
                self._tasks[i] = task
                return

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

        await form_state.open_update_dialog(
            task=task,
            callback_after_close=self.add_or_update_task
        )

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
            warning = " This will also delete all its subtasks."

        delete_dialog_state.open_dialog(
            title="Delete Task",
            content=f"Are you sure you want to delete this task?{warning}",
            action=lambda: self._delete_action(task.id)
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
