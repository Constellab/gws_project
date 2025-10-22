
import reflex as rx
from gws_reflex_main import main_component

from ..common.kanban.kanban import kanban_board
from ..common.page_layout import page_layout
from .kanban_state import KanbanState


def kanban_page() -> rx.Component:
    """Create the kanban page showing all tasks across all projects.

    This page displays all tasks accessible to the current user in a kanban board
    format with columns for TODO, DOING, and DONE statuses.

    :return: The kanban page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.fragment(
                rx.vstack(
                    # Page header
                    rx.heading(
                        "Task Board",
                        size="6",
                        margin_bottom="1rem"
                    ),
                    rx.text(
                        "View and manage all your tasks across all projects",
                        size="2",
                        color="gray",
                        margin_bottom="2rem"
                    ),

                    # Kanban board
                    rx.cond(
                        KanbanState.tasks.length() > 0,
                        kanban_board(
                            board_data=KanbanState.kanban_board_data,
                            disable_column_drag=True,
                            on_card_move=KanbanState.handle_card_move,
                            width="100%",
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
                                rx.text(
                                    "Tasks from all your projects will appear here",
                                    size="2",
                                    color="gray",
                                    margin_top="0.25rem"
                                ),
                                spacing="2",
                                align="center"
                            ),
                            padding="4rem"
                        )
                    ),

                    width="100%",
                    spacing="3",
                    align_items="start",
                )
            )
        )
    )
