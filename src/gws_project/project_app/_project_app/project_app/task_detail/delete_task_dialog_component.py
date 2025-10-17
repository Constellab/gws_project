import reflex as rx
from gws_reflex_main import confirm_dialog


def delete_task_dialog() -> rx.Component:
    """Create the delete task confirmation dialog.

    This component provides a confirmation dialog for deleting a task.
    The dialog is controlled by the DeleteTaskDialogState.dialog_opened state.

    :return: The delete task dialog component
    :rtype: rx.Component
    """
    from .delete_task_dialog_state import DeleteTaskDialogState

    return confirm_dialog(
        state=DeleteTaskDialogState,
        title="Delete Task",
        content=rx.vstack(
            rx.text(
                "Are you sure you want to delete this task?",
                size="3"
            ),
            rx.cond(
                DeleteTaskDialogState.has_subtasks,
                rx.callout(
                    "This task has subtasks. Deleting it will also delete all subtasks.",
                    icon="triangle_alert",
                    color_scheme="orange",
                    size="1"
                )
            ),
            rx.text(
                "This action cannot be undone.",
                size="2",
                color="gray"
            ),
            spacing="3",
            width="100%"
        )
    )
