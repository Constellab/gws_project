from typing import Callable, List

import reflex as rx
from gws_project.task.task_dto import TaskDTO
from gws_reflex_main import user_inline_component

from ..common.task_components import task_icon_component
from .priority_chip_component import priority_chip
from .status_chip_component import status_chip


def task_table_component(
    tasks: List[TaskDTO],
    actions_menu_fn: Callable[[TaskDTO], rx.Component],
    empty_message: str = "No tasks found"
) -> rx.Component:
    """Create a reusable task table component.

    This component displays a table of tasks with columns for title, description,
    dates, status, priority, assigned user, and a customizable actions menu.

    :param tasks: List of task DTOs to display
    :type tasks: List[TaskDTO]
    :param actions_menu_fn: Function that takes a TaskDTO and returns an actions menu component
    :type actions_menu_fn: Callable[[TaskDTO], rx.Component]
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
                    lambda task: _task_row(task, actions_menu_fn)
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


def _task_row(task: TaskDTO, actions_menu_fn: Callable[[TaskDTO], rx.Component]) -> rx.Component:
    """Create a table row for a single task.

    :param task: The task data transfer object
    :type task: TaskDTO
    :param actions_menu_fn: Function that generates the actions menu for the task
    :type actions_menu_fn: Callable[[TaskDTO], rx.Component]
    :return: The task row component
    :rtype: rx.Component
    """
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                # Icon indicating if task allows subtasks
                task_icon_component(task, size=16),
                rx.link(
                    task.title,
                    href=f"/task/{task.id}",
                    color="blue",
                    text_decoration="underline",
                    cursor="pointer"
                ),
                spacing="2",
                align="center"
            )
        ),
        rx.table.cell(
            rx.text(
                task.description,
                max_width="300px",
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
        rx.table.cell(actions_menu_fn(task)),
    )
