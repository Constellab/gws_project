import reflex as rx
from gws_project.project_app._project_app.project_app.common.progress_bar import progress_bar
from gws_project.task.task_dto import TaskDTO
from gws_reflex_main import user_inline_component

from ..priority_chip_component import priority_chip
from ..project_app_router import ProjectAppRouter
from ..status_chip_component import status_chip
from .task_actions_menu import task_actions_menu
from .task_components import task_icon_component


def task_table_component(
    tasks: list[TaskDTO], empty_message: str = "No tasks found"
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
                    rx.table.column_header_cell("Dates"),
                    rx.table.column_header_cell("Status"),
                    rx.table.column_header_cell("Priority"),
                    rx.table.column_header_cell("Assigned To"),
                    rx.table.column_header_cell("Actions", width="100px", justify="end"),
                ),
            ),
            rx.table.body(rx.foreach(tasks, lambda task: _task_row(task))),
            width="100%",
            variant="surface",
        ),
        # Empty state when no tasks
        rx.center(
            rx.vstack(
                rx.icon("list_todo", size=48, color="gray"),
                rx.text(empty_message, size="4", color="gray", margin_top="1rem"),
                spacing="2",
                align="center",
            ),
            padding="3rem",
            width="100%",
        ),
    )


def _task_row(task: TaskDTO) -> rx.Component:
    """Create a table row for a single task.

    :param task: The task data transfer object
    :type task: TaskDTO
    :return: The task row component
    :rtype: rx.Component
    """
    from ...task_list.task_list_state import TaskListState

    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                # Icon indicating if task allows subtasks
                task_icon_component(task, size="3"),
                rx.text(
                    task.title,
                ),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(rx.moment(task.start_date, format="MMM D, YYYY"), size="2"),
                rx.text(rx.moment(task.end_date, format="MMM D, YYYY"), size="2"),
                spacing="1",
                align="start",
            )
        ),
        rx.table.cell(
            rx.vstack(
                status_chip(task.status),
                progress_bar(task.progress, width="50px"),
                spacing="2",
                align="start",
                width="100%",
            )
        ),
        rx.table.cell(priority_chip(task.priority)),
        rx.table.cell(user_inline_component(task.assign_to)),
        rx.table.cell(
            rx.box(
                task_actions_menu(
                    on_update=lambda: TaskListState.open_update_task_dialog(task.id),
                    on_delete=lambda: TaskListState.open_delete_task_dialog(task),
                    on_change_type=lambda: TaskListState.open_change_task_type_dialog(task),
                    stop_propagation=True,
                ),
                display="flex",
                justify_content="flex-end",
                align_items="center",
            )
        ),
        style={":hover": {"background_color": "var(--gray-3)"}, "cursor": "pointer"},
        on_click=lambda: rx.redirect(ProjectAppRouter.get_task_detail_url(task.id)),
    )


