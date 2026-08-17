import reflex as rx
from gws_reflex_main import main_component
from gws_reflex_main.components.reflex_user_components import user_select

from ..common.kanban.kanban import (
    PRIORITY_COLOR_MAP,
    STATUS_COLOR_MAP,
    USER_COLOR_MAP,
    kanban_board,
)
from ..common.page_layout import page_layout
from .kanban_quick_add_state import KanbanQuickAddState
from .kanban_state import KanbanState


def _filter_bar() -> rx.Component:
    """Create the filter bar with search, project, user, and date filters in a row.

    :return: The filter bar component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Text search input
        rx.input(
            placeholder="Title",
            value=KanbanState.search_text,
            on_change=KanbanState.handle_search_change,
            min_width="300px",
        ),
        # Project filter select
        rx.select.root(
            rx.select.trigger(
                placeholder="All Projects",
                width="200px",
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
        ),
        # User filter select
        user_select(
            users=KanbanState.available_users,
            placeholder="All Users",
            value=KanbanState.selected_user_id,
            on_change=KanbanState.handle_user_change,
            width="200px",
        ),
        # Company filter select
        rx.select.root(
            rx.select.trigger(
                placeholder="All Companies",
                width="200px",
            ),
            rx.select.content(
                rx.foreach(
                    KanbanState.company_options,
                    lambda opt: rx.select.item(
                        opt[1],
                        value=opt[0],
                    ),
                )
            ),
            value=KanbanState.selected_company_id,
            on_change=KanbanState.handle_company_change,
        ),
        # Date filter select
        rx.select.root(
            rx.select.trigger(
                width="200px",
            ),
            rx.select.content(
                rx.select.item("All", value="all"),
                rx.select.item("Last Week", value="last_week"),
                rx.select.item("Current Week", value="current_week"),
                rx.select.item("Next Week", value="next_week"),
                rx.select.item("Current Month", value="current_month"),
            ),
            value=KanbanState.selected_date_filter,
            on_change=KanbanState.handle_date_filter_change,
        ),
        # Show Backlog toggle (off by default to avoid cluttering the board)
        rx.text(
            rx.switch(
                checked=KanbanState.show_backlog,
                on_change=KanbanState.handle_show_backlog_change,
            ),
            "Show Backlog",
            as_="label",
            size="2",
            style={"display": "flex", "align-items": "center", "gap": "8px", "cursor": "pointer"},
        ),
        # Clear filters button
        rx.button(
            "Clear",
            on_click=KanbanState.clear_filters,
            variant="surface",
            size="2",
            color_scheme="gray",
            radius="large",
        ),
        width="100%",
        spacing="3",
        wrap="wrap",
        margin_top="16px",
        align="center",
    )


def kanban_page() -> rx.Component:
    """Create the kanban page showing all tasks across all projects.

    This page displays all tasks accessible to the current user in a kanban board
    format with columns for TODO, DOING, and DONE statuses (plus an optional Backlog
    column, hidden by default, toggled via the "Show Backlog" switch).

    :return: The kanban page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.vstack(
                # Filter bar
                _filter_bar(),
                # Kanban board
                kanban_board(
                    board_data=KanbanState.kanban_board_data,
                    status_color_map=STATUS_COLOR_MAP,
                    priority_color_map=PRIORITY_COLOR_MAP,
                    user_color_map=USER_COLOR_MAP,
                    disable_column_drag=True,
                    on_card_move=KanbanState.handle_card_move,
                    on_card_click=KanbanState.handle_card_click,
                    quick_add_column_id=KanbanQuickAddState.active_column_id,
                    quick_add_title=KanbanQuickAddState.title,
                    quick_add_can_submit=KanbanQuickAddState.can_submit,
                    quick_add_is_creating=KanbanQuickAddState.is_creating,
                    quick_add_browse_open=KanbanQuickAddState.browse_open,
                    quick_add_current_project_title=KanbanQuickAddState.current_project_title,
                    quick_add_breadcrumb_tasks=KanbanQuickAddState.breadcrumb_tasks,
                    quick_add_projects=KanbanQuickAddState.projects,
                    quick_add_tasks=KanbanQuickAddState.tasks,
                    on_quick_add_open=KanbanQuickAddState.open_quick_add,
                    on_quick_add_cancel=KanbanQuickAddState.cancel_quick_add,
                    on_quick_add_title_change=KanbanQuickAddState.set_title,
                    on_quick_add_toggle_browse=KanbanQuickAddState.toggle_browse,
                    on_quick_add_navigate=KanbanQuickAddState.navigate,
                    on_quick_add_select_here=KanbanQuickAddState.select_here,
                    on_quick_add_submit=KanbanQuickAddState.submit,
                    width="100%",
                    flex="1",
                    class_name="kanban-board",
                ),
                width="100%",
                spacing="3",
                align_items="start",
                height="100%",
            ),
            header_content=rx.heading(
                "Task Board",
                size="6",
            ),
            height="100vh",
        )
    )
