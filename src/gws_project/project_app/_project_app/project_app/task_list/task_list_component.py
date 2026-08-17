import reflex as rx
from gws_project.task.task_dto import TaskPriority, TaskStatus
from gws_reflex_main import translate
from gws_reflex_main.components.reflex_user_components import user_select

from ..common.tasks.task_card_component import task_card_list_component
from . import task_list_translations  # noqa: F401  (side effect: registers translations)
from .task_list_state import TaskListState


def _filter_bar() -> rx.Component:
    """Create the filter bar with search, status, priority, and assignee filters.

    :return: The filter bar component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Text search input
        rx.input(
            rx.input.slot(rx.icon("search", size=16)),
            placeholder=translate("task_list.search_placeholder"),
            value=TaskListState.search_text,
            on_change=TaskListState.handle_search_change,
            min_width="250px",
        ),
        # Status filter select
        rx.select.root(
            rx.select.trigger(placeholder=translate("task_list.all_statuses"), width="160px"),
            rx.select.content(
                rx.select.item(translate("task_list.all_statuses"), value=""),
                *[rx.select.item(status.value, value=status.value) for status in TaskStatus],
            ),
            value=TaskListState.selected_status_filter,
            on_change=TaskListState.handle_status_filter_change,
        ),
        # Priority filter select
        rx.select.root(
            rx.select.trigger(placeholder=translate("task_list.all_priorities"), width="160px"),
            rx.select.content(
                rx.select.item(translate("task_list.all_priorities"), value=""),
                *[rx.select.item(priority.value, value=priority.value) for priority in TaskPriority],
            ),
            value=TaskListState.selected_priority_filter,
            on_change=TaskListState.handle_priority_filter_change,
        ),
        # Assignee filter select
        user_select(
            users=TaskListState.available_users,
            placeholder=translate("task_list.all_assignees"),
            value=TaskListState.selected_assignee_id,
            on_change=TaskListState.handle_assignee_change,
            width="200px",
        ),
        # Clear filters button
        rx.button(
            translate("task_list.clear"),
            on_click=TaskListState.clear_filters,
            variant="surface",
            size="2",
            color_scheme="gray",
            radius="large",
        ),
        width="100%",
        spacing="3",
        wrap="wrap",
    )


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
                        rx.text(
                            translate("task_list.loading"), size="3", color="gray", margin_top="1rem"
                        ),
                        spacing="2",
                        align="center",
                    ),
                    padding="3rem",
                    width="100%",
                    flex="1",
                    min_height="0",
                ),
                task_card_list_component(
                    tasks=TaskListState.get_tasks, empty_message=translate("task_list.empty")
                ),
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


def task_list_content() -> rx.Component:
    """Create the tasks list content without header.

    The header (title and action button) is managed at the tab level
    in the project detail page.

    :return: The tasks list content component
    :rtype: rx.Component
    """
    return rx.vstack(
        _filter_bar(),
        task_list_component(),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
    )
