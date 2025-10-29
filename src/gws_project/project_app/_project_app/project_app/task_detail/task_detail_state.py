from typing import Optional

import reflex as rx
from gws_core import RichTextDTO
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from gws_project.project.project_dto import ProjectDTO
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskDTO, TaskPriority, TaskStatus
from gws_project.task.task_service import TaskService

from ..common.project_page_state import ProjectPageState
from ..task_form.task_form_dialog_state import TaskFormDialogState
from ..task_list.task_list_state import TaskListState


class TaskDetailState(ReflexMainState):
    """State for managing the task detail page.

    This state handles fetching and displaying the details of a single task
    based on the task ID from the URL.
    """

    description_edit_mode: bool = False  # Track if description is in edit mode

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

        # Get the Task object (not DTO) from ProjectPageState
        project_page_state = await self.get_state(ProjectPageState)
        task = await project_page_state.task()

        if not task:
            yield rx.toast.error("Task not found")
            return

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

    def toggle_description_edit_mode(self):
        """Toggle the description edit mode."""
        self.description_edit_mode = not self.description_edit_mode

    @rx.event
    async def handle_description_change(self, event_data: dict):
        """Handle changes from the rich text component and update the task description.

        Args:
            event_data: Dictionary containing the RichTextDTO data
        """
        # Convert event data to RichTextDTO
        description_dto = RichTextDTO.from_json(event_data)

        # Get current task
        task = await self.task
        if not task:
            return

        # Update the task description
        with await self.authenticate_user():
            task_service = TaskService()
            task_service.update_task_description(
                task.id,
                description_dto
            )

        # Reload the task to reflect changes
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()

    @rx.event
    async def open_delete_task_dialog(self):
        """Open the delete task confirmation dialog."""
        task = await self.task
        if not task:
            yield
            return

        delete_dialog_state = await self.get_state(ConfirmDialogState)

        # Build confirmation message
        warning = ""
        if task.allow_subtasks:
            warning = " This will also delete all its subtasks."

        delete_dialog_state.open_dialog(
            title="Delete Task",
            content=f"Are you sure you want to delete this task?{warning}",
            action=self._delete_task_action
        )

    async def _delete_task_action(self):
        """Action to delete the task after confirmation."""
        task = await self.task
        if not task:
            yield
            return

        # Delete the task
        with await self.authenticate_user():
            task_service = TaskService()
            task_service.delete_task(task.id)

        # Show success toast
        yield rx.toast.success("Task deleted successfully")

        # Navigate based on context
        project_page_state = await self.get_state(ProjectPageState)
        current_object = await project_page_state.get_object()

        if isinstance(current_object, Task):
            if current_object.parent_task:
                # If we are on a subtask's detail page, redirect to parent task
                yield rx.redirect(f"/task/{current_object.parent_task.id}")
            else:
                # If we are on the deleted task's detail page, redirect to project detail
                yield rx.redirect(f"/project/{current_object.project.id}")

    async def update_status(self, new_status: str):
        """Handle status change for the task.

        :param new_status: The new status string
        :type new_status: str
        """
        task = await self.task
        if not task:
            yield rx.toast.error("Task not found")
            return

        # create TaskStatus enum from string
        task_status = TaskStatus[new_status]

        with await self.authenticate_user():
            task_service = TaskService()
            task_service.update_status(task.id, task_status)

        # Refresh the current task
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()

    async def update_priority(self, new_priority: str):
        """Handle priority change for the task.

        :param new_priority: The new priority string
        :type new_priority: str
        """
        task = await self.task
        if not task:
            yield rx.toast.error("Task not found")
            return

        # create TaskPriority enum from string
        task_priority = TaskPriority[new_priority]

        with await self.authenticate_user():
            task_service = TaskService()
            task_service.update_priority(task.id, task_priority)

        # Refresh the current task
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()
