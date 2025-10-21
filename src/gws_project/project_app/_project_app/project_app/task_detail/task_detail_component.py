import reflex as rx
from gws_project.task.task_dto import TaskDTO
from gws_reflex_main import main_component, user_inline_component

from ..common.breadcrumb.breadcrumb_component import breadcrumb_component
from ..common.priority_chip_component import priority_chip
from ..common.status_chip_component import status_chip
from ..task_form.task_form_dialog_component import task_form_dialog
from ..task_form.task_form_dialog_state import TaskFormDialogState
from .delete_task_dialog_component import delete_task_dialog
from .delete_task_dialog_state import DeleteTaskDialogState
from .subtask_list.subtask_list_component import subtask_list_component
from .task_detail_state import TaskDetailState


def header(task: TaskDTO) -> rx.Component:
    """Create the header component for the task detail page.

    This component displays the task title, dates, and assigned user.

    :param task: The task data transfer object
    :type task: TaskDTO
    :return: The header component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Title
        rx.heading(
            task.title,
            size="8",
            margin_bottom="0.5rem"
        ),
        # Calendar icon with dates
        rx.icon("calendar", size=18),
        rx.text(
            rx.moment(
                task.start_date,
                format="MMM D, YYYY"
            ),
            " - ",
            rx.moment(
                task.end_date,
                format="MMM D, YYYY"
            ),
            size="3",
            color="gray"
        ),
        # Assigned user
        rx.text("Assigned to:", size="3", color="gray"),
        user_inline_component(task.assign_to),
        spacing="2",
        align="center",
    )


def parent_task_section() -> rx.Component:
    """Create the parent task section.

    This section displays information about the parent task if the current task is a subtask.

    :return: The parent task section component
    :rtype: rx.Component
    """
    return rx.cond(
        TaskDetailState.parent_task,
        rx.vstack(
            rx.heading(
                "Parent Task",
                size="5",
            ),
            rx.card(
                rx.hstack(
                    rx.vstack(
                        rx.link(
                            rx.text(
                                TaskDetailState.parent_task.title,
                                size="4",
                                weight="bold",
                                color="blue"
                            ),
                            href=f"/task/{TaskDetailState.parent_task.id}",
                            style={"text_decoration": "none"}
                        ),
                        rx.text(
                            TaskDetailState.parent_task.description,
                            size="2",
                            color="gray",
                            max_width="600px",
                            overflow="hidden",
                            text_overflow="ellipsis",
                            white_space="nowrap"
                        ),
                        spacing="1",
                        align_items="start"
                    ),
                    rx.spacer(),
                    rx.hstack(
                        status_chip(TaskDetailState.parent_task.status, size="2"),
                        priority_chip(TaskDetailState.parent_task.priority, size="2"),
                        spacing="2",
                        align="center"
                    ),
                    width="100%",
                    align="center"
                ),
                width="100%"
            ),
            width="100%",
            spacing="2",
            align_items="start"
        )
    )


def task_info_section() -> rx.Component:
    """Create the task information section.

    :return: The task information section component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Status and Priority badges
        rx.hstack(
            rx.vstack(
                rx.text("Status", size="2", weight="bold", color="gray"),
                status_chip(TaskDetailState.task.status, size="2"),
                spacing="1",
                align_items="start"
            ),
            rx.vstack(
                rx.text("Priority", size="2", weight="bold", color="gray"),
                priority_chip(TaskDetailState.task.priority, size="2"),
                spacing="1",
                align_items="start"
            ),
            spacing="4",
            align="center"
        ),
        # Description
        rx.vstack(
            rx.text("Description", size="3", weight="bold"),
            rx.text(
                TaskDetailState.task.description,
                size="3",
                color="gray"
            ),
            spacing="1",
            align_items="start",
            width="100%"
        ),
        # Creator and last modified info
        rx.hstack(
            rx.hstack(
                rx.text("Created by:", size="2", color="gray"),
                user_inline_component(TaskDetailState.task.created_by),
                rx.text(
                    "on",
                    rx.moment(TaskDetailState.task.created_at, format="MMM D, YYYY HH:mm"),
                    size="2",
                    color="gray"
                ),
                spacing="1",
                align="center"
            ),
            rx.hstack(
                rx.text("Last modified by:", size="2", color="gray"),
                user_inline_component(TaskDetailState.task.last_modified_by),
                rx.text(
                    "on",
                    rx.moment(TaskDetailState.task.last_modified_at, format="MMM D, YYYY HH:mm"),
                    size="2",
                    color="gray"
                ),
                spacing="1",
                align="center"
            ),
            spacing="4",
            wrap="wrap"
        ),
        width="100%",
        spacing="3",
        align_items="start"
    )


def subtasks_section() -> rx.Component:
    """Create the subtasks section with subtask list and create button.

    :return: The subtasks section component
    :rtype: rx.Component
    """
    return rx.cond(
        TaskDetailState.task.allow_subtasks,
        rx.vstack(
            # Header with title and create button
            rx.hstack(
                rx.heading(
                    "Subtasks",
                    size="5",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    "Create Subtask",
                    variant="soft",
                    on_click=lambda: TaskFormDialogState.open_create_sub_dialog(
                        TaskDetailState.task.id,
                        TaskDetailState.project
                    )
                ),
                width="100%",
                align="center",
            ),
            # Subtask list component
            subtask_list_component(),
            width="100%",
            spacing="3",
            align_items="start",
        )
    )


def task_detail_page() -> rx.Component:
    """Create the task detail page component.

    This component displays all details of a single task including
    title, description, dates, status, priority, assigned user, and subtasks if allowed.

    :return: The task detail page component
    :rtype: rx.Component
    """
    return main_component(
        rx.vstack(
            # Breadcrumb navigation
            breadcrumb_component(),

            # Header with action buttons
            rx.hstack(
                rx.spacer(),
                rx.cond(
                    TaskDetailState.task,
                    rx.hstack(
                        rx.button(
                            rx.icon("pencil", size=18),
                            "Update Task",
                            on_click=lambda: TaskFormDialogState.open_update_dialog(TaskDetailState.task)
                        ),
                        rx.button(
                            rx.icon("trash_2", size=18),
                            "Delete",
                            color_scheme="red",
                            variant="soft",
                            on_click=lambda: DeleteTaskDialogState.open_dialog_with_task(
                                TaskDetailState.task.id,
                                TaskDetailState.task.allow_subtasks
                            )
                        ),
                        spacing="2"
                    ),
                ),
                justify="end",
                align="center",
                width="100%",
                margin_bottom="1rem"
            ),

            # Error message display
            rx.cond(
                TaskDetailState.error_message != "",
                rx.callout(
                    TaskDetailState.error_message,
                    icon="triangle_alert",
                    color_scheme="red",
                    role="alert",
                    margin_bottom="1rem"
                ),
            ),

            # Loading indicator
            rx.cond(
                TaskDetailState.is_loading,
                rx.center(
                    rx.spinner(size="3"),
                    padding="2rem"
                ),
                # Task details
                rx.cond(
                    TaskDetailState.task,
                    rx.vstack(
                        # Header with title, dates, and assigned user
                        header(TaskDetailState.task),

                        # Parent task section (only if task has a parent)
                        parent_task_section(),

                        # Task information section
                        task_info_section(),

                        # Subtasks section (only if task allows subtasks)
                        subtasks_section(),

                        width="100%",
                        spacing="4"
                    ),
                )
            ),

            width="100%",
            spacing="4",
            padding="2rem"
        ),
        # Add the task form dialog
        task_form_dialog(),
        # Add the delete confirmation dialog
        delete_task_dialog()
    )
