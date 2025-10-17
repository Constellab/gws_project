import reflex as rx
from gws_project.task.task_service import TaskService
from gws_reflex_main import ConfirmDialogState, ReflexMainState


class DeleteTaskDialogState(ConfirmDialogState, rx.State):
    """State management for the delete task confirmation dialog."""

    # Task ID to delete
    _task_id: str = ""

    # Flag to indicate if the task has subtasks
    has_subtasks: bool = False

    @rx.event
    def open_dialog_with_task(self, task_id: str, has_subtasks: bool):
        """Open the delete confirmation dialog with a task ID.

        :param task_id: The ID of the task to delete
        :type task_id: str
        :param has_subtasks: Flag indicating if the task has subtasks
        :type has_subtasks: bool
        """
        self._task_id = task_id
        self.has_subtasks = has_subtasks
        self.open_dialog()

    @rx.event
    async def confirm_action(self):
        """Handle the delete action when the user confirms."""
        if not self._task_id:
            yield
            return

        try:
            main_state = await self.get_state(ReflexMainState)
            # Delete the task
            with await main_state.authenticate_user():
                task_service = TaskService()
                task_service.delete_task(self._task_id)

            # Show success toast
            yield rx.toast.success("Task deleted successfully")

            # Close the dialog
            self.dialog_opened = False
            self._task_id = ""
            self.has_subtasks = False

            # Navigate back to project list
            yield rx.redirect("/")

        except Exception as e:
            yield rx.toast.error(f"Error deleting task: {str(e)}")
