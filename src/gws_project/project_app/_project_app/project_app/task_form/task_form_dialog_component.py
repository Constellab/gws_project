import reflex as rx
from gws_project.task.task_dto import TaskPriority, TaskStatus
from gws_reflex_main import form_dialog_component, user_select

from .task_form_dialog_state import TaskFormDialogState


def _form_content() -> rx.Component:
    """Form content for entering task details."""
    return rx.vstack(
        # Title field
        rx.vstack(
            rx.text("Task Title*", size="2", weight="bold"),
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

        # Assign to field (shown in both create and update modes)
        rx.vstack(
            rx.text("Assign To", size="2", weight="bold"),
            user_select(
                users=TaskFormDialogState.users,
                placeholder="Select a user (default to yourself)",
                name="assign_to_id",
                default_value=TaskFormDialogState.form_assign_to_id,
                width="100%",
            ),
            width="100%",
            spacing="1"
        ),

        # Task type radio buttons (shown in both create root and create sub modes, hidden in update mode)
        rx.cond(
            ~TaskFormDialogState.is_update_mode,
            rx.vstack(
                rx.text("Task Type*", size="2", weight="bold"),
                rx.radio.root(
                    rx.hstack(
                        rx.radio.item(
                            rx.hstack(
                                rx.text("📋 Single task", size="2"),
                                spacing="2",
                                align="center"
                            ),
                            value="without_children"
                        ),
                        rx.radio.item(
                            rx.hstack(
                                rx.text("📁 Task with subtasks", size="2"),
                                spacing="2",
                                align="center"
                            ),
                            value="with_children"
                        ),
                        spacing="4"
                    ),
                    default_value=TaskFormDialogState.selected_task_type,
                    value=TaskFormDialogState.selected_task_type,
                    on_change=TaskFormDialogState.set_selected_task_type,
                    name="allow_subtasks"
                ),
                width="100%",
                spacing="1"
            )
        ),

        # Date fields and Priority/Status (conditionally shown)
        rx.cond(
            TaskFormDialogState.should_show_dates_and_priority,
            rx.vstack(
                # Date fields
                rx.hstack(
                    rx.vstack(
                        rx.text("Start Date*", size="2", weight="bold"),
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
                        rx.text("End Date*", size="2", weight="bold"),
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


                # Create mode: show both status and priority
                rx.hstack(
                    rx.vstack(
                        rx.text("Status*", size="2", weight="bold"),
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
                        rx.text("Priority*", size="2", weight="bold"),
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
                ),
                width="100%",
            ),

            # When dates and priority are hidden, show a message explaining auto-calculation
            rx.vstack(
                rx.callout.root(
                    rx.callout.icon(
                        rx.icon(tag="info", size=16)
                    ),
                    rx.callout.text(
                        "Dates, status, and priority are automatically calculated from all descendant tasks.",
                        size="2"
                    ),
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
            TaskFormDialogState.is_update_mode, "Update Task", rx.cond(
                TaskFormDialogState.is_create_sub_mode, "Create New Subtask", "Create New Task")
        ),
        form_content=_form_content(),
        max_width="600px"
    )
