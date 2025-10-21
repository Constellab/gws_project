
import reflex as rx

from ..common.task_table_component import task_table_component
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
    )
