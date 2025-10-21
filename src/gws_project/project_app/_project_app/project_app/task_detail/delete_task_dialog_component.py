import reflex as rx
from gws_reflex_main import confirm_dialog

from .delete_task_dialog_state import DeleteTaskDialogState


def delete_task_dialog() -> rx.Component:
    """Create the delete task confirmation dialog.

    This component provides a confirmation dialog for deleting a task.
    The dialog is controlled by the DeleteTaskDialogState.dialog_opened state.

    :return: The delete task dialog component
    :rtype: rx.Component
    """

    return confirm_dialog(
        state=DeleteTaskDialogState,
        title="Delete Task",
        content="Are you sure you want to delete this task?",
    )
