
import reflex as rx
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskDTO
from gws_project.task.task_service import TaskService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.project_page_state import ProjectPageState
from ..task_list.task_list_state import TaskListState


class DeleteTaskDialogState(ConfirmDialogState, rx.State):
    """State management for the delete task confirmation dialog."""

    # Task to be deleted
    _task: TaskDTO | None = None

    # Flag to indicate if the task has subtasks
    has_subtasks: bool = False

    @rx.event
    def open_dialog_with_task(self, task: TaskDTO):
        """Open the delete confirmation dialog with a task ID.

        :param task_id: The ID of the task to delete
        :type task_id: str
        :param has_subtasks: Flag indicating if the task has subtasks
        :type has_subtasks: bool
        """
        self._task = task
        self.has_subtasks = task.allow_subtasks
        self.open_dialog()

    async def _on_confirm(self):
        """Handle the delete action when the user confirms."""
        if not self._task:
            yield
            return

        async with self:
            main_state = await self.get_state(ReflexMainState)

        # Delete the task
        with await main_state.authenticate_user():
            task_service = TaskService()
            task_service.delete_task(self._task.id)

        # Show success toast
        yield rx.toast.success("Task deleted successfully")

        # Clear the task state
        async with self:

            project_page_state = await self.get_state(ProjectPageState)

            current_object = await project_page_state.get_object()

            if isinstance(current_object, Task) and current_object.id == self._task.id:
                if current_object.parent_task:
                    # If we are on a subtask's detail page, redirect to parent task
                    yield rx.redirect(f"/task/{current_object.parent_task.id}")
                else:
                    # If we are on the deleted task's detail page, redirect to project detail
                    yield rx.redirect(f"/project/{current_object.project.id}")
            else:
                # Otherwise, refresh the project page to reflect the deletion
                task_list_state = await self.get_state(TaskListState)
                task_list_state.delete_task(task_id=self._task.id)

            self._task = None
            self.has_subtasks = False
