
import reflex as rx

from ..common.task_table_component import task_table_component
from ..project_detail.project_detail_state import ProjectDetailState
from .task_list_state import TaskListState


def task_list_component() -> rx.Component:
    """Create the task list component displaying all tasks for a project.

    This component displays a table of tasks with columns for title, description,
    dates, status, priority, assigned user, and actions menu.

    :return: The task list component
    :rtype: rx.Component
    """
    return rx.vstack(
        task_table_component(
            tasks=TaskListState.get_tasks,
            empty_message="No tasks found"
        ),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
        overflow_y="auto",
    )


def task_list_view() -> rx.Component:
    """Create the tasks list view with header and content.

    :return: The tasks list view component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Tasks header with create button
        rx.hstack(
            rx.heading("Tasks", size="4", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "Create Task",
                variant="soft",
                size="2",
                on_click=ProjectDetailState.open_create_task_dialog
            ),
            width="100%",
            align="center"

        ),
        # Tasks list content
        task_list_component(),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
    )
