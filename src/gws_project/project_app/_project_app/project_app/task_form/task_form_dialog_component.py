import reflex as rx
from gws_core.apps.reflex._gws_reflex.gws_reflex_main.components.reflex_form_dialog_component import \
    form_dialog_component
from gws_project.task.task_dto import TaskPriority, TaskStatus
from gws_reflex_main import user_select

from .task_form_dialog_state import TaskFormDialogState


def _form_content() -> rx.Component:
    """Form content for entering task details."""
    return rx.vstack(
        # Title field
        rx.vstack(
            rx.text("Task Title", size="2", weight="bold"),
            rx.input(
                placeholder="Enter task title",
                name="title",
                required=True,
                width="100%",
                default_value=TaskFormDialogState.form_title
            ),
            width="100%",
            spacing="1"
        ),

        # Description field
        rx.vstack(
            rx.text("Description", size="2", weight="bold"),
            rx.text_area(
                placeholder="Enter task description",
                name="description",
                required=True,
                width="100%",
                rows="4",
                default_value=TaskFormDialogState.form_description
            ),
            width="100%",
            spacing="1"
        ),

        rx.cond(
            TaskFormDialogState.is_create_mode,
            # Assign to field
            rx.vstack(
                rx.text("Assign To", size="2", weight="bold"),
                user_select(
                    users=TaskFormDialogState.users,
                    placeholder="Select a user (optional)",
                    name="assign_to_id",
                    default_value=TaskFormDialogState.form_assign_to_id
                ),
                width="100%",
                spacing="1"
            ),

        ),
        # Date fields
        rx.hstack(
            rx.vstack(
                rx.text("Start Date", size="2", weight="bold"),
                rx.input(
                    type="date",
                    name="start_date",
                    required=True,
                    width="100%",
                    default_value=TaskFormDialogState.form_start_date,
                    min=TaskFormDialogState.get_min_start_date,
                    max=TaskFormDialogState.get_max_end_date,
                ),
                width="100%",
                spacing="1"
            ),

            rx.vstack(
                rx.text("End Date", size="2", weight="bold"),
                rx.input(
                    type="date",
                    name="end_date",
                    required=True,
                    width="100%",
                    default_value=TaskFormDialogState.form_end_date,
                    min=TaskFormDialogState.get_min_start_date,
                    max=TaskFormDialogState.get_max_end_date,
                ),
                width="100%",
                spacing="1"
            ),
            width="100%",
            spacing="3"
        ),

        # Priority and Status (Status only shown in create mode)
        rx.cond(
            TaskFormDialogState.is_update_mode,
            # Update mode: only show priority
            rx.vstack(
                rx.text("Priority", size="2", weight="bold"),
                rx.select(
                    [priority.value for priority in TaskPriority],
                    name="priority",
                    default_value=TaskFormDialogState.form_priority,
                    width="100%",
                ),
                width="100%",
                spacing="1"
            ),
            # Create mode: show both status and priority
            rx.hstack(
                rx.vstack(
                    rx.text("Status", size="2", weight="bold"),
                    rx.select(
                        [status.value for status in TaskStatus],
                        name="status",
                        default_value=TaskFormDialogState.form_status,
                        width="100%",
                    ),
                    width="100%",
                    spacing="1"
                ),

                rx.vstack(
                    rx.text("Priority", size="2", weight="bold"),
                    rx.select(
                        [priority.value for priority in TaskPriority],
                        name="priority",
                        default_value=TaskFormDialogState.form_priority,
                        width="100%",
                    ),
                    width="100%",
                    spacing="1"
                ),
                width="100%",
                spacing="3"
            )
        ),

        # Allow subtasks checkbox (only in create root mode, not in create sub or update mode)
        rx.cond(
            ~TaskFormDialogState.is_update_mode & ~TaskFormDialogState.is_create_sub_mode,
            rx.vstack(
                rx.hstack(
                    rx.checkbox(
                        name="allow_subtasks",
                        default_checked=TaskFormDialogState.form_allow_subtasks,
                        value="true"
                    ),
                    rx.text("Allow subtasks", size="2"),
                    spacing="2",
                    align="center"
                ),
                width="100%",
                spacing="1"
            )
        ),

        width="100%",
        spacing="3"
    )


def task_form_dialog() -> rx.Component:
    """Dialog component for creating or updating a task.

    This component provides the dialog (without a trigger button).
    The dialog is controlled by the TaskFormDialogState.dialog_opened state.

    :return: The task form dialog component
    :rtype: rx.Component
    """
    return form_dialog_component(
        state=TaskFormDialogState,
        title=rx.cond(
            TaskFormDialogState.is_update_mode,
            "Update Task",
            rx.cond(
                TaskFormDialogState.is_create_sub_mode,
                "Create New Subtask",
                "Create New Root Task"
            )
        ),
        description=rx.cond(
            TaskFormDialogState.is_update_mode,
            "Update the task details below.",
            rx.cond(
                TaskFormDialogState.is_create_sub_mode,
                "Fill in the details below to create a new subtask under the parent task.",
                "Fill in the details below to create a new root task for this project."
            )
        ),
        form_content=_form_content(),
        max_width="600px"
    )
