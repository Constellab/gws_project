
import reflex as rx
from gws_reflex_main import main_component

from ..common.kanban.kanban import kanban_board
from ..common.page_layout import page_layout
from .kanban_state import KanbanState


def _filter_bar() -> rx.Component:
    """Create the filter bar with search, project, and user filters in a row.

    :return: The filter bar component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Text search input
        rx.input(
            placeholder="Search tasks...",
            value=KanbanState.search_text,
            on_change=KanbanState.handle_search_change,
            min_width="300px",
        ),

        # Project filter select
        rx.select.root(
            rx.select.trigger(
                placeholder="All Projects",
            ),
            rx.select.content(
                rx.foreach(
                    KanbanState.project_options,
                    lambda opt: rx.select.item(
                        opt[1],
                        value=opt[0],
                    ),
                )
            ),
            value=KanbanState.selected_project_id,
            on_change=KanbanState.handle_project_change,
            width="200px",
        ),

        # User filter select
        rx.select.root(
            rx.select.trigger(
                placeholder="All Users",
            ),
            rx.select.content(
                rx.foreach(
                    KanbanState.user_options,
                    lambda opt: rx.select.item(
                        opt[1],
                        value=opt[0],
                    ),
                )
            ),
            value=KanbanState.selected_user_id,
            on_change=KanbanState.handle_user_change,
            width="200px",
        ),

        # Clear filters button
        rx.button(
            "Clear",
            on_click=KanbanState.clear_filters,
            variant="outline",
            size="2",
        ),

        width="100%",
        spacing="3",
    )


def kanban_page() -> rx.Component:
    """Create the kanban page showing all tasks across all projects.

    This page displays all tasks accessible to the current user in a kanban board
    format with columns for TODO, DOING, and DONE statuses.

    :return: The kanban page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.vstack(
                # Page header
                rx.heading(
                    "Task Board",
                    size="6",
                ),

                # Filter bar
                _filter_bar(),

                # Kanban board
                rx.cond(
                    KanbanState.tasks.length() > 0,
                    kanban_board(
                        board_data=KanbanState.kanban_board_data,
                        disable_column_drag=True,
                        on_card_move=KanbanState.handle_card_move,
                        on_card_click=KanbanState.handle_card_click,
                        width="100%",
                        flex="1",
                        class_name="kanban-board",
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
                        width="100%",
                    )
                ),

                width="100%",
                spacing="3",
                align_items="start",
                height="100%",
            ),
            height="100vh",
        )
    )
