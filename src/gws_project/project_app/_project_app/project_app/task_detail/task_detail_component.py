import reflex as rx
from gws_reflex_main import main_component, user_inline_component
from gws_reflex_main.gws_components import rich_text_component

from ..common.detail_page_layout import detail_page_layout
from ..common.page_layout import page_layout
from ..common.priority_chip_component import priority_chip
from ..common.status_chip_component import status_chip
from ..common.task_components import task_icon_component
from ..task_description_dialog.task_description_dialog_component import \
    task_description_dialog
from ..task_description_dialog.task_description_dialog_state import \
    TaskDescriptionDialogState
from ..task_form.task_form_dialog_component import task_form_dialog
from ..task_list.task_list_component import task_list_component
from .task_detail_state import TaskDetailState


def main_content_area() -> rx.Component:
    """Create the main content area (left side) with title, description, and subtasks.

    :return: The main content area component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Title row with icon and action menu
        rx.hstack(
            # Icon indicating if task allows subtasks
            task_icon_component(TaskDetailState.task, size=24),
            # Title
            rx.heading(
                TaskDetailState.task.title,
                size="8",
            ),
            rx.spacer(),
            # Action menu (Update and Delete)
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.icon("ellipsis-vertical", size=18),
                        variant="soft",
                        color_scheme="gray"
                    )
                ),
                rx.menu.content(
                    rx.menu.item(
                        rx.icon("pencil", size=16),
                        "Update Task",
                        on_click=TaskDetailState.open_update_task_dialog
                    ),
                    rx.menu.item(
                        rx.icon("file-text", size=16),
                        "Update Description",
                        on_click=lambda: TaskDescriptionDialogState.open_dialog_with_task(TaskDetailState.task)
                    ),
                    rx.menu.separator(),
                    rx.menu.item(
                        rx.icon("trash_2", size=16),
                        "Delete",
                        color="red",
                        on_click=TaskDetailState.open_delete_task_dialog
                    ),
                ),
            ),
            width="100%",
            align="center",
            spacing="2"
        ),

        # Description section
        rx.vstack(
            rx.heading("Description", size="4", weight="bold", margin_top="1.5rem"),
            rx.cond(
                TaskDetailState.task.description,
                rich_text_component(
                    initial_value=TaskDetailState.task.description,
                    disabled=True,
                    min_height="100px",
                ),
                rx.text(
                    "No description provided",
                    size="3",
                    color="gray",
                    font_style="italic"
                )
            ),
            width="100%",
            spacing="2",
            align_items="start"
        ),

        # Subtasks section (only if task allows subtasks)
        rx.cond(
            TaskDetailState.task.allow_subtasks,
            rx.vstack(
                # Header with title and create button
                rx.hstack(
                    rx.heading(
                        "Subtasks",
                        size="5",
                        margin_top="1.5rem"
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Create Subtask",
                        variant="soft",
                        size="2",
                        on_click=TaskDetailState.open_create_subtask_dialog
                    ),
                    width="100%",
                    align="center",
                ),
                # Subtask list component
                task_list_component(),
                width="100%",
                spacing="3",
                align_items="start",
            )
        ),

        width="100%",
        spacing="3",
        align_items="start",
        flex="1"
    )


def details_sidebar() -> rx.Component:
    """Create the details sidebar (right side) with technical information.

    :return: The details sidebar component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.heading("Details", size="5", margin_bottom="1rem"),

        # Details grid - single parent grid with all fields
        rx.grid(
            # Parent task (conditional row)
            rx.cond(
                TaskDetailState.parent_task,
                rx.fragment(
                    rx.text("Parent task", size="2", color="gray", weight="medium"),
                    rx.link(
                        TaskDetailState.parent_task.title,
                        href=f"/task/{TaskDetailState.parent_task.id}",
                        size="2",
                    ),
                )
            ),

            # Assigned to
            rx.text("Assigned to", size="2", color="gray", weight="medium"),
            user_inline_component(TaskDetailState.task.assign_to),

            # Status
            rx.text("Status", size="2", color="gray", weight="medium"),
            rx.box(status_chip(
                TaskDetailState.task.status,
                on_status_change=TaskDetailState.update_status,
                allow_subtask=TaskDetailState.task.allow_subtasks,
                size="2"
            )),

            # Priority
            rx.text("Priority", size="2", color="gray", weight="medium"),
            rx.box(priority_chip(
                TaskDetailState.task.priority,
                on_priority_change=TaskDetailState.update_priority,
                allow_subtask=TaskDetailState.task.allow_subtasks,
                size="2"
            )),

            # Start date
            rx.text("Start date", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(TaskDetailState.task.start_date, format="MMM D, YYYY"),
                size="2"
            ),

            # End date
            rx.text("End date", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(TaskDetailState.task.end_date, format="MMM D, YYYY"),
                size="2"
            ),

            # Divider before technical info (spans 2 columns)
            rx.divider(margin_top="0.5rem", margin_bottom="0.5rem", grid_column="span 2"),

            # Created by
            rx.text("Created by", size="2", color="gray", weight="medium"),
            user_inline_component(TaskDetailState.task.created_by),

            # Created at
            rx.text("Created at", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(TaskDetailState.task.created_at, format="MMM D, YYYY HH:mm"),
                size="2",
            ),

            # Last modified by
            rx.text("Last modified by", size="2", color="gray", weight="medium"),
            user_inline_component(TaskDetailState.task.last_modified_by),

            # Last modified at
            rx.text("Last modified at", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(TaskDetailState.task.last_modified_at, format="MMM D, YYYY HH:mm"),
                size="2",
            ),

            columns="2",
            spacing="3",
            width="100%",
            row_gap="1rem"
        ),

        width="100%",
        spacing="3",
        align_items="start"
    )


def task_detail() -> rx.Component:
    """Create the task detail page component.

    This component displays all details of a single task using a Jira-like layout
    with main content on the left and a details sidebar on the right.

    :return: The task detail page component
    :rtype: rx.Component
    """
    return rx.cond(
        TaskDetailState.task,
        detail_page_layout(
            main_content=main_content_area(),
            sidebar_content=details_sidebar()
        ),
    )


def task_detail_page() -> rx.Component:
    """Create the task detail page component.

    This component displays all details of a single task using a Jira-like layout
    with main content on the left and a details sidebar on the right.

    :return: The task detail page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.vstack(
                # Task details in two-column layout with breadcrumb
                task_detail(),
                width="100%",
            )
        ),
        # Add the task form dialog
        task_form_dialog(),
        # Add the description dialog
        task_description_dialog(),
    )
