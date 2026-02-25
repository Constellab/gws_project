import reflex as rx

from ..common.tasks.task_card_component import task_card_list_component
from ..common.tasks.task_table_component import task_table_component
from ..project_detail.project_detail_state import ProjectDetailState
from .task_list_state import TaskListState


def task_list_component() -> rx.Component:
    """Create the task list component displaying all tasks for a project.

    This component displays tasks as small cards. The table view is kept
    available via task_table_list_component() for alternative usage.

    The component uses a key based on current_url_id to force remount when URL changes,
    ensuring tasks are reloaded when navigating between tasks.

    :return: The task list component
    :rtype: rx.Component
    """
    return rx.box(
        rx.vstack(
            rx.cond(
                TaskListState.is_loading & (TaskListState.get_tasks.length() == 0),
                # Loading state - show spinner
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text("Loading tasks...", size="3", color="gray", margin_top="1rem"),
                        spacing="2",
                        align="center",
                    ),
                    padding="3rem",
                    width="100%",
                    flex="1",
                    min_height="0",
                ),
                task_card_list_component(tasks=TaskListState.get_tasks, empty_message="No tasks found"),
            ),
            # Trigger background fetch when component mounts
            on_mount=TaskListState.fetch_tasks_on_mount,
            # full height but not overflow parent
            width="100%",
            flex="1",
            min_height="0",
            overflow_y="auto",
        ),
        # Key forces remount when URL changes
        key=TaskListState.current_object_id,
        width="100%",
        flex="1",
        min_height="0",
    )


def task_table_list_component() -> rx.Component:
    """Create the task list component using a table layout.

    This is the original table-based task list, kept for alternative usage.

    :return: The task table list component
    :rtype: rx.Component
    """
    return rx.box(
        rx.vstack(
            rx.cond(
                TaskListState.is_loading & (TaskListState.get_tasks.length() == 0),
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text("Loading tasks...", size="3", color="gray", margin_top="1rem"),
                        spacing="2",
                        align="center",
                    ),
                    padding="3rem",
                    width="100%",
                    flex="1",
                    min_height="0",
                ),
                task_table_component(tasks=TaskListState.get_tasks, empty_message="No tasks found"),
            ),
            on_mount=TaskListState.fetch_tasks_on_mount,
            width="100%",
            flex="1",
            min_height="0",
            overflow_y="auto",
        ),
        key=TaskListState.current_object_id,
        width="100%",
        flex="1",
        min_height="0",
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
                on_click=ProjectDetailState.open_create_task_dialog,
            ),
            width="100%",
            align="center",
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
