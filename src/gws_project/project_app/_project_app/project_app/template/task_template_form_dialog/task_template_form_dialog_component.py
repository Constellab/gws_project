import reflex as rx
from gws_project.task.task_dto import TaskPriority
from gws_reflex_main import form_dialog_component

from .task_template_form_dialog_state import TaskTemplateFormDialogState


def _form_content() -> rx.Component:
    """Form content for entering task template details."""
    return rx.vstack(
        # Title field
        rx.vstack(
            rx.text("Task Template Title*", size="2", weight="bold"),
            rx.input(
                placeholder="Enter task template title",
                name="title",
                required=True,
                width="100%",
                default_value=TaskTemplateFormDialogState.form_title
            ),
            width="100%",
            spacing="1"
        ),

        # Task type radio buttons (only in create root mode, not in create sub or update mode)
        rx.cond(
            ~TaskTemplateFormDialogState.is_update_mode & ~TaskTemplateFormDialogState.is_create_sub_mode,
            rx.vstack(
                rx.text("Task Type*", size="2", weight="bold"),
                rx.radio.root(
                    rx.hstack(
                        rx.radio.item(
                            rx.hstack(
                                rx.icon(tag="file", size=16),
                                rx.text("Single task", size="2"),
                                spacing="2",
                                align="center"
                            ),
                            value="without_children"
                        ),
                        rx.radio.item(
                            rx.hstack(
                                rx.icon(tag="folder", size=16),
                                rx.text("Task with subtasks", size="2"),
                                spacing="2",
                                align="center"
                            ),
                            value="with_children"
                        ),
                        spacing="4"
                    ),
                    default_value=TaskTemplateFormDialogState.selected_task_type,
                    value=TaskTemplateFormDialogState.selected_task_type,
                    on_change=TaskTemplateFormDialogState.set_selected_task_type,
                    name="allow_subtasks"
                ),
                width="100%",
                spacing="1"
            )
        ),

        # Date offset and duration fields (conditionally shown)
        rx.cond(
            TaskTemplateFormDialogState.should_show_dates_and_priority,
            rx.vstack(
                # Date offset and duration fields
                rx.hstack(
                    rx.vstack(
                        rx.text("Start Date Offset (days)*", size="2", weight="bold"),
                        rx.input(
                            type="number",
                            name="start_date_offset",
                            required=True,
                            width="100%",
                            default_value=TaskTemplateFormDialogState.form_start_date_offset.to_string(),
                            min="0",
                            placeholder="Days from project start"
                        ),
                        width="100%",
                        spacing="1"
                    ),

                    rx.vstack(
                        rx.text("Duration (days)*", size="2", weight="bold"),
                        rx.input(
                            type="number",
                            name="duration_days",
                            required=True,
                            width="100%",
                            default_value=TaskTemplateFormDialogState.form_duration_days.to_string(),
                            min="1",
                            placeholder="Task duration"
                        ),
                        width="100%",
                        spacing="1"
                    ),
                    width="100%",
                    spacing="3"
                ),

                # Priority field
                rx.vstack(
                    rx.text("Priority*", size="2", weight="bold"),
                    rx.select(
                        [priority.value for priority in TaskPriority],
                        name="priority",
                        default_value=TaskTemplateFormDialogState.form_priority,
                        width="100%",
                    ),
                    width="100%",
                    spacing="1"
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
                        rx.cond(
                            TaskTemplateFormDialogState.is_create_sub_mode,
                            "Date offsets, duration, and priority will be managed by the parent task and calculated based on subtask values.",
                            rx.cond(
                                TaskTemplateFormDialogState.is_parent_task_in_update_mode,
                                "Date offsets, duration, and priority are automatically calculated from subtasks.",
                                "Date offsets, duration, and priority will be automatically calculated from subtasks once you add them."
                            )
                        ),
                        size="2"
                    ),
                ),
                width="100%",
                spacing="1"
            )
        ),

        # Assign to role field
        rx.vstack(
            rx.text("Assign to Role (optional)", size="2", weight="bold"),
            rx.text(
                "Specify a role name to assign this task to a specific role. When creating a project from this template, you'll be able to assign users to each role.",
                size="1",
                color="gray",
            ),
            rx.input(
                placeholder="e.g., project_manager, team_member",
                name="assign_to_role",
                width="100%",
                default_value=TaskTemplateFormDialogState.form_assign_to_role
            ),
            width="100%",
            spacing="1"
        ),

        width="100%",
        spacing="3"
    )


def task_template_form_dialog() -> rx.Component:
    """Dialog component for creating or updating a task template.

    This component provides the dialog (without a trigger button).
    The dialog is controlled by the TaskTemplateFormDialogState.dialog_opened state.

    :return: The task template form dialog component
    :rtype: rx.Component
    """
    return form_dialog_component(
        state=TaskTemplateFormDialogState, title=rx.cond(
            TaskTemplateFormDialogState.is_update_mode, "Update Task Template", rx.cond(
                TaskTemplateFormDialogState.is_create_sub_mode, "Create New Subtask Template",
                "Create New Task Template")),
        description=rx.cond(
            TaskTemplateFormDialogState.is_update_mode, rx.cond(
                TaskTemplateFormDialogState.is_parent_task_in_update_mode,
                "Update the task template details below. Date offsets, duration, and priority are automatically calculated from subtasks.",
                "Update the task template details below."),
            rx.cond(
                TaskTemplateFormDialogState.is_create_sub_mode,
                "Fill in the details below to create a new subtask template. Date offsets, duration, and priority will be managed by the parent task.",
                "Fill in the details below to create a new task template for this project template.")),
        form_content=_form_content(),
        max_width="600px")
