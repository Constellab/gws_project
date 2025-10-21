from typing import List

import reflex as rx
from gws_project.task.task_dto import TaskDTO
from gws_reflex_main import ReflexUtils, user_inline_component

from ..common.task_components import task_icon_component
from .priority_chip_component import priority_chip
from .status_chip_component import status_chip


def task_table_component(
    tasks: List[TaskDTO],
    empty_message: str = "No tasks found"
) -> rx.Component:
    """Create a reusable task table component.

    This component displays a table of tasks with columns for title, description,
    dates, status, priority, assigned user, and a customizable actions menu.

    :param tasks: List of task DTOs to display
    :type tasks: List[TaskDTO]
    :param empty_message: Message to display when no tasks are found (default: "No tasks found")
    :type empty_message: str
    :return: The task table component
    :rtype: rx.Component
    """
    return rx.cond(
        tasks.length() > 0,
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
                    tasks,
                    lambda task: _task_row(task)
                )
            ),
            width="100%",
            variant="surface",
        ),
        # Empty state when no tasks
        rx.center(
            rx.vstack(
                rx.icon("list_todo", size=48, color="gray"),
                rx.text(
                    empty_message,
                    size="4",
                    color="gray",
                    margin_top="1rem"
                ),
                spacing="2",
                align="center"
            ),
            padding="3rem",
            width="100%"
        )
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
            rx.hstack(
                # Icon indicating if task allows subtasks
                task_icon_component(task, size=16),
                rx.text(
                    task.title,
                ),
                spacing="2",
                align="center"
            )
        ),
        rx.table.cell(
            rx.text(
                task.description,
                style=ReflexUtils.multiline_ellipsis_css(lines=3, max_width="300px")
            ),
            max_width="300px"
        ),
        rx.table.cell(rx.moment(task.start_date, format="MMM D, YYYY")),
        rx.table.cell(rx.moment(task.end_date, format="MMM D, YYYY")),
        rx.table.cell(status_chip(task.status)),
        rx.table.cell(priority_chip(task.priority)),
        rx.table.cell(user_inline_component(task.assign_to)),
        rx.table.cell(_actions_menu(task)),
        style={
            ":hover": {"background_color": "var(--gray-3)"},
            "cursor": "pointer"
        },
        on_click=lambda: rx.redirect(f"/task/{task.id}")
    )


def _actions_menu(subtask: TaskDTO) -> rx.Component:
    """Create the actions menu for a subtask.

    :param subtask: The subtask data transfer object
    :type subtask: TaskDTO
    :return: The actions menu component
    :rtype: rx.Component
    """
    from ..task_list.task_list_state import TaskListState

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
                on_click=lambda: TaskListState.open_update_task_dialog(subtask)
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash_2", size=16),
                "Delete",
                color="red",
                on_click=lambda: TaskListState.open_delete_task_dialog(subtask)
            ),
            on_click=lambda: rx.stop_propagation,  # Prevent row click event
        ),
    )
