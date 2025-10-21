
import reflex as rx

from ..common.task_table_component import task_table_component
from ..task_form.task_form_dialog_state import TaskFormDialogState
from .task_list_state import TaskDTO, TaskListState


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
            actions_menu_fn=_task_actions_menu,
            empty_message="No tasks found"
        ),
        width="100%",
        spacing="3",
        align_items="start",
    )


def _task_actions_menu(task: TaskDTO) -> rx.Component:
    """Create the actions menu for a task.

    :param task: The task data transfer object
    :type task: TaskDTO
    :return: The actions menu component
    :rtype: rx.Component
    """

    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("ellipsis-vertical", size=18),
                variant="soft",
                size="2"
            )
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("pencil", size=16),
                "Update",
                on_click=lambda: TaskFormDialogState.open_update_dialog(task)
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash_2", size=16),
                "Delete",
                color="red",
                on_click=lambda: TaskListState.delete_task(task.id)
            ),
        ),
    )
