from typing import Optional

import reflex as rx
from gws_project.project.project_dto import ProjectDTO
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskDTO
from gws_reflex_main import ReflexMainState

from ..common.project_page_state import ProjectPageState
from ..task_form.task_form_dialog_state import TaskFormDialogState
from ..task_list.task_list_state import TaskListState


class TaskDetailState(ReflexMainState):
    """State for managing the task detail page.

    This state handles fetching and displaying the details of a single task
    based on the task ID from the URL.
    """

    @rx.var
    async def task(self) -> Optional[TaskDTO]:
        """Return the current task DTO.

        :return: The current task DTO
        :rtype: Optional[TaskDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_object = await project_page_state.task()
        if current_object:
            return current_object.to_dto()
        return None

    @rx.var
    async def project(self) -> Optional[ProjectDTO]:
        """Return the current project DTO.

        :return: The current project DTO
        :rtype: Optional[ProjectDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_object = await project_page_state.project()
        if current_object:
            return current_object.to_dto()
        return None

    @rx.var
    async def parent_task(self) -> Optional[TaskDTO]:
        """Return the parent task DTO if this is a subtask.

        :return: The parent task DTO or None
        :rtype: Optional[TaskDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_task = await project_page_state.task()

        if not current_task or not current_task.parent_task:
            return None

        return current_task.parent_task.to_dto()

    async def open_create_subtask_dialog(self):
        """Open the create subtask dialog."""

        form_state = await self.get_state(TaskFormDialogState)

        task = await self.task

        await form_state.open_create_sub_dialog(
            parent_task_id=task.id,
            project=await self.project,
            callback_after_close=self._on_create_subtask_dialog_close
        )

    async def _on_create_subtask_dialog_close(self, task: Task):
        """Callback after the create subtask dialog is closed to refresh subtasks."""
        # Currently, no specific action is needed here.
        task_list_state = await self.get_state(TaskListState)

        task_list_state.add_or_update_task(task)

    async def open_update_task_dialog(self):
        """Open the update task dialog for this task."""
        form_state = await self.get_state(TaskFormDialogState)
        task = await self.task

        await form_state.open_update_dialog(
            task=task,
            callback_after_close=self._on_update_task_dialog_close
        )

    async def _on_update_task_dialog_close(self, _: Task):
        """Callback after the update task dialog is closed to refresh the task.

        :param task: The updated task
        :type task: Task
        """
        # Refresh the current task by reloading from the page state
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()
