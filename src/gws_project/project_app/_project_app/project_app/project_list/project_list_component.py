import reflex as rx
from gws_reflex_main import main_component, user_inline_component
from gws_reflex_main.components.reflex_user_components import user_select

from ..common.page_layout import page_layout
from ..project_form_dialog.project_form_dialog_component import create_project_dialog
from .project_list_state import ProjectDTO, ProjectListState


def _filter_bar() -> rx.Component:
    """Create the filter bar with search and manager filters.

    :return: The filter bar component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Text search input
        rx.input(
            placeholder="Search projects...",
            value=ProjectListState.search_text,
            on_change=ProjectListState.handle_search_change,
            min_width="300px",
        ),
        # Manager filter select
        user_select(
            users=ProjectListState.available_managers,
            placeholder="All Managers",
            value=ProjectListState.selected_manager_id,
            on_change=ProjectListState.handle_manager_change,
            width="200px",
        ),
        # Clear filters button
        rx.button(
            "Clear",
            on_click=ProjectListState.clear_filters,
            variant="outline",
            size="2",
        ),
        width="100%",
        spacing="3",
        wrap="wrap",
    )


def project_list_page() -> rx.Component:
    """Create the project list page component.

    This component displays a table of projects for the current user
    with columns for title, description, dates, project manager, and creator.
    Includes filters for searching by project name and filtering by manager.

    :return: The project list page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.vstack(
                # Filter bar
                _filter_bar(),
                # Error message display
                rx.cond(
                    ProjectListState.error_message != "",
                    rx.callout(
                        ProjectListState.error_message,
                        icon="triangle_alert",
                        color_scheme="red",
                        role="alert",
                        margin_bottom="1rem",
                    ),
                ),
                # Loading indicator
                rx.cond(
                    ProjectListState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="2rem"),
                    # Project table
                    rx.cond(
                        ProjectListState.projects.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Title"),
                                    rx.table.column_header_cell("Start Date"),
                                    rx.table.column_header_cell("End Date"),
                                    rx.table.column_header_cell("Manager"),
                                    rx.table.column_header_cell("Created At"),
                                ),
                            ),
                            rx.table.body(rx.foreach(ProjectListState.projects, _row)),
                            width="100%",
                            variant="surface",
                        ),
                        # Empty state when no projects
                        rx.center(
                            rx.vstack(
                                rx.icon("folder_open", size=48, color="gray"),
                                rx.text("No projects found", size="4", color="gray", margin_top="1rem"),
                                spacing="2",
                                align="center",
                            ),
                            padding="3rem",
                            width="100%",
                        ),
                    ),
                ),
                width="100%",
                spacing="4",
            ),
            header_content=rx.hstack(
                rx.heading("My projects", size="6"),
                create_project_dialog(),
                justify="between",
                align="center",
                width="100%",
            ),
        )
    )


def _row(project: ProjectDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(project.title),
        ),
        rx.table.cell(rx.moment(project.start_date, format="MMM D, YYYY")),
        rx.table.cell(rx.moment(project.end_date, format="MMM D, YYYY")),
        rx.table.cell(user_inline_component(project.project_manager)),
        rx.table.cell(rx.moment(project.created_at, format="MMM D, YYYY")),
        style={":hover": {"background_color": "var(--gray-3)"}, "cursor": "pointer"},
        on_click=lambda: ProjectListState.go_to_project(project.id),
    )
