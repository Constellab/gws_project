import reflex as rx
from gws_reflex_main import user_inline_component

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
        # Subtask table
        rx.cond(
            TaskDetailState.subtasks.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Title"),
                        rx.table.column_header_cell("Description"),
                        rx.table.column_header_cell("Start Date"),
                        rx.table.column_header_cell("End Date"),
                        rx.table.column_header_cell("Status"),
                        rx.table.column_header_cell("Priority"),
                        rx.table.column_header_cell("Assigned To"),
                        rx.table.column_header_cell("Actions", width="100px"),
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        TaskDetailState.subtasks,
                        lambda subtask: _subtask_row(subtask)
                    )
                ),
                width="100%",
                style={"table": {"vertical_align": "middle"}},
            ),
            # Empty state when no subtasks
            rx.center(
                rx.vstack(
                    rx.icon("list_todo", size=40, color="gray"),
                    rx.text(
                        "No subtasks found",
                        size="3",
                        color="gray",
                        margin_top="0.5rem"
                    ),
                    spacing="2",
                    align="center"
                ),
                padding="2rem"
            )
        ),

        width="100%",
        spacing="3",
        align_items="start",
    )


def _subtask_row(subtask: TaskDTO) -> rx.Component:
    """Create a table row for a single subtask.

    :param subtask: The subtask data transfer object
    :type subtask: TaskDTO
    :return: The subtask row component
    :rtype: rx.Component
    """
    return rx.table.row(
        rx.table.cell(
            rx.link(
                rx.text(
                    subtask.title,
                    weight="medium",
                    color="blue"
                ),
                href=f"/task/{subtask.id}",
                style={"text_decoration": "none"}
            )
        ),
        rx.table.cell(
            rx.text(
                subtask.description,
                max_width="200px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap"
            )
        ),
        rx.table.cell(rx.moment(subtask.start_date, format="MMM D, YYYY")),
        rx.table.cell(rx.moment(subtask.end_date, format="MMM D, YYYY")),
        rx.table.cell(_status_badge(subtask.status)),
        rx.table.cell(_priority_badge(subtask.priority)),
        rx.table.cell(user_inline_component(subtask.assign_to)),
        rx.table.cell(_subtask_actions_menu(subtask)),
    )


def _status_badge(status: str) -> rx.Component:
    """Create a status badge component.

    :param status: The task status
    :type status: str
    :return: The status badge component
    :rtype: rx.Component
    """
    color_map = {
        "TODO": "gray",
        "DOING": "blue",
        "DONE": "green"
    }
    return rx.badge(
        status,
        color_scheme=color_map.get(status, "gray"),
        variant="soft"
    )


def _priority_badge(priority: str) -> rx.Component:
    """Create a priority badge component.

    :param priority: The task priority
    :type priority: str
    :return: The priority badge component
    :rtype: rx.Component
    """
    color_map = {
        "HIGH": "red",
        "MEDIUM": "yellow",
        "LOW": "gray"
    }
    return rx.badge(
        priority,
        color_scheme=color_map.get(priority, "gray"),
        variant="soft"
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
