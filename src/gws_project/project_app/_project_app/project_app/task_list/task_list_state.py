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

    @rx.var
    async def get_tasks(self) -> List[TaskDTO]:

        project_state = await self.get_state(ProjectPageState)
        url_param = await project_state.get_url_params()

        previous_id = self._url_params.id if self._url_params else None
        current_id = url_param.id if url_param else None
        if previous_id != current_id:
            self._url_params = url_param
            task_service = TaskService()
            with await self.authenticate_user():
                if url_param and url_param.type == "project":
                    self._tasks = task_service.get_root_tasks_of_project(url_param.id)
                elif url_param and url_param.type == "task":
                    self._tasks = task_service.get_subtasks(url_param.id)
                else:
                    self._tasks = []

        return [task.to_dto() for task in self._tasks]

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
