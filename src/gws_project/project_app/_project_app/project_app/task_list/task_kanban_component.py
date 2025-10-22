"""Kanban view component for tasks."""


import reflex as rx

from ..common.kanban.kanban import kanban_board
from .task_list_state import TaskListState


def task_kanban_component() -> rx.Component:
    """Create a Kanban board view for tasks.

    This component displays tasks in a Kanban board format with columns
    for TODO, DOING, and DONE statuses.

    :return: The task Kanban component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Kanban board
        rx.cond(
            TaskListState.get_tasks.length() > 0,
            kanban_board(
                board_data=TaskListState.kanban_board_data,
                disable_column_drag=True,
                on_card_move=TaskListState.handle_card_move,
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
