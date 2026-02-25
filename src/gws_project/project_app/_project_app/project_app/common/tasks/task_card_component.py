"""Task card component for displaying tasks as small cards."""

import reflex as rx
from gws_project.task.task_dto import TaskDTO, TaskStatus
from gws_reflex_main import user_profile_picture

from ...task_list.task_list_state import TaskListState
from ..priority_chip_component import priority_chip
from ..project_app_router import ProjectAppRouter
from .task_actions_menu import task_actions_menu
from .task_components import task_icon_component
from .task_status_chip_component import task_status_chip


def _get_status_background(status: TaskStatus) -> rx.Var:
    """Get the background color for a task card icon based on status.

    :param status: The task status
    :type status: TaskStatus
    :return: The background color
    :rtype: rx.Var
    """
    return rx.match(
        status,
        (TaskStatus.DONE, "var(--accent-3)"),
        "var(--gray-3)",
    )


def _task_card(task: TaskDTO) -> rx.Component:
    """Create a small card for a single task.

    Inspired by the example.jsx task card design:
    - Icon + title + dates on the left
    - Priority, status badges and assignee avatar on the right
    - Progress bar at the bottom

    :param task: The task data transfer object
    :type task: TaskDTO
    :return: The task card component
    :rtype: rx.Component
    """

    return rx.box(
        rx.vstack(
            # Top row: icon+title on left, badges+avatar on right
            rx.hstack(
                # Left side: icon + title + dates
                rx.hstack(
                    # Task type icon
                    rx.box(
                        task_icon_component(task, size="3"),
                        width="32px",
                        height="32px",
                        border_radius="8px",
                        background=_get_status_background(task.status),
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text(
                            task.title,
                            weight="bold",
                            size="2",
                            style=rx.cond(
                                task.status == TaskStatus.DONE,
                                {"color": "var(--gray-9)"},
                                {},
                            ),
                            trim="both",
                        ),
                        rx.hstack(
                            rx.text(
                                rx.moment(task.start_date, format="MMM D, YYYY"),
                                size="1",
                                color="var(--gray-9)",
                            ),
                            rx.text("→", size="1", color="var(--gray-7)"),
                            rx.text(
                                rx.moment(task.end_date, format="MMM D, YYYY"),
                                size="1",
                                color="var(--gray-9)",
                            ),
                            spacing="1",
                            align="center",
                        ),
                        spacing="1",
                        align_items="start",
                    ),
                    spacing="3",
                    align="center",
                    flex="1",
                    min_width="0",
                ),
                # Right side: priority, status, assignee, actions
                rx.hstack(
                    priority_chip(task.priority, size="1", show_icon=True),
                    task_status_chip(task.status, size="1", show_icon=True),
                    user_profile_picture(task.assign_to, size="small"),
                    task_actions_menu(
                        on_update=lambda: TaskListState.open_update_task_dialog(task.id),
                        on_delete=lambda: TaskListState.open_delete_task_dialog(task),
                        on_change_type=lambda: TaskListState.open_change_task_type_dialog(task),
                        stop_propagation=True,
                    ),
                    spacing="2",
                    align="center",
                    flex_shrink="0",
                ),
                width="100%",
                align="center",
                justify="between",
            ),
            # Bottom: progress bar (no percentage text, thin bar)
            rx.box(
                rx.box(
                    width=f"{task.progress}%",
                    height="100%",
                    background="var(--accent-9)",
                    border_radius="4px",
                    transition="width 0.3s ease",
                ),
                width="100%",
                height="6px",
                background="var(--gray-3)",
                border_radius="4px",
                overflow="hidden",
            ),
            spacing="3",
            width="100%",
        ),
        padding="16px 20px",
        background="white",
        border_radius="14px",
        border="1px solid var(--gray-4)",
        width="100%",
        cursor="pointer",
        transition="all 0.2s ease",
        _hover={"border_color": "var(--gray-6)", "box_shadow": "0 2px 8px var(--gray-a3)"},
        on_click=lambda: rx.redirect(ProjectAppRouter.get_task_detail_url(task.id)),
    )


def task_card_list_component(
    tasks: list[TaskDTO], empty_message: str = "No tasks found"
) -> rx.Component:
    """Create a reusable task card list component.

    Displays tasks as small cards stacked vertically, similar to the example.jsx
    project detail view.

    :param tasks: List of task DTOs to display
    :type tasks: list[TaskDTO]
    :param empty_message: Message to display when no tasks are found
    :type empty_message: str
    :return: The task card list component
    :rtype: rx.Component
    """
    return rx.cond(
        tasks.length() > 0,
        rx.vstack(
            rx.foreach(tasks, _task_card),
            spacing="2",
            width="100%",
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
