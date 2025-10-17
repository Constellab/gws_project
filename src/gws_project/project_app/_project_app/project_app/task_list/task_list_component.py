
import reflex as rx
from gws_reflex_main import user_inline_component

from .task_list_state import TaskDTO, TaskListState


def task_list_component() -> rx.Component:
    """Create the task list component displaying all tasks for a project.

    This component displays a table of tasks with columns for title, description,
    dates, status, priority, assigned user, and actions menu.

    :return: The task list component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Error message display
        rx.cond(
            TaskListState.error_message != "",
            rx.callout(
                TaskListState.error_message,
                icon="triangle_alert",
                color_scheme="red",
                role="alert",
            ),
        ),

        # Loading indicator
        rx.cond(
            TaskListState.is_loading,
            rx.center(
                rx.spinner(size="3"),
                padding="1rem"
            ),
            # Task table
            rx.cond(
                TaskListState.tasks.length() > 0,
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
                            TaskListState.tasks,
                            lambda task: _task_row(task)
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
        rx.table.cell(_status_badge(task.status)),
        rx.table.cell(_priority_badge(task.priority)),
        rx.table.cell(user_inline_component(task.assign_to)),
        rx.table.cell(_task_actions_menu(task)),
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


def _task_actions_menu(task: TaskDTO) -> rx.Component:
    """Create the actions menu for a task.

    :param task: The task data transfer object
    :type task: TaskDTO
    :return: The actions menu component
    :rtype: rx.Component
    """
    from ..task_form.task_form_dialog_state import TaskFormDialogState

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
