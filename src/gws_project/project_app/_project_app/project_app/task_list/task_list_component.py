
import reflex as rx
from gws_reflex_main import user_inline_component

from ..common.priority_chip_component import priority_chip
from ..common.status_chip_component import status_chip
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
        # Task table
        rx.cond(
            TaskListState.get_tasks.length() > 0,
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
                        TaskListState.get_tasks,
                        _task_row
                    )
                ),
                width="100%",
                style={"table": {"vertical_align": "middle"}},
            ),
            # Empty state when no tasks
            rx.center(
                rx.vstack(
                    rx.icon("list_todo", size=40, color="gray"),
                    rx.text(
                        "No tasks found",
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


def _task_row(task: TaskDTO) -> rx.Component:
    """Create a table row for a single task.

    :param task: The task data transfer object
    :type task: TaskDTO
    :return: The task row component
    :rtype: rx.Component
    """
    return rx.table.row(
        rx.table.cell(
            rx.link(
                rx.text(
                    task.title,
                    weight="medium",
                    color="blue"
                ),
                href=f"/task/{task.id}",
                style={"text_decoration": "none"}
            )
        ),
        rx.table.cell(
            rx.text(
                task.description,
                max_width="200px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap"
            )
        ),
        rx.table.cell(rx.moment(task.start_date, format="MMM D, YYYY")),
        rx.table.cell(rx.moment(task.end_date, format="MMM D, YYYY")),
        rx.table.cell(status_chip(task.status)),
        rx.table.cell(priority_chip(task.priority)),
        rx.table.cell(user_inline_component(task.assign_to)),
        rx.table.cell(_task_actions_menu(task)),
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
