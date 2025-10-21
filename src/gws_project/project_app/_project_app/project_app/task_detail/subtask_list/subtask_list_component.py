import reflex as rx

from ...common.task_table_component import task_table_component
from ..task_detail_state import TaskDetailState, TaskDTO
from .subtask_list_state import SubtaskListState


def subtask_list_component() -> rx.Component:
    """Create the subtask list component displaying all subtasks for a task.

    This component displays a table of subtasks with columns for title, description,
    dates, status, priority, assigned user, and actions menu.

    :return: The subtask list component
    :rtype: rx.Component
    """
    return rx.vstack(
        task_table_component(
            tasks=TaskDetailState.subtasks,
            actions_menu_fn=_subtask_actions_menu,
            empty_message="No subtasks found"
        ),
        width="100%",
        spacing="3",
        align_items="start",
    )


def _subtask_actions_menu(subtask: TaskDTO) -> rx.Component:
    """Create the actions menu for a subtask.

    :param subtask: The subtask data transfer object
    :type subtask: TaskDTO
    :return: The actions menu component
    :rtype: rx.Component
    """
    from ...task_form.task_form_dialog_state import TaskFormDialogState

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
                on_click=lambda: TaskFormDialogState.open_update_dialog(subtask)
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash_2", size=16),
                "Delete",
                color="red",
                on_click=lambda: SubtaskListState.delete_subtask(subtask.id)
            ),
        ),
    )
