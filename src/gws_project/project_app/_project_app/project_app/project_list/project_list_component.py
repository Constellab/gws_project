
import reflex as rx
from gws_reflex_main import main_component, user_inline_component

from ..create_project_dialog.project_form_dialog_component import \
    create_project_dialog
from .project_list_state import ProjectDTO, ProjectListState


def project_list_page() -> rx.Component:
    """Create the project list page component.

    This component displays a table of projects for the current user
    with columns for title, description, dates, project manager, and creator.

    :return: The project list page component
    :rtype: rx.Component
    """
    return main_component(
        rx.vstack(
            # Header with title and create button
            rx.hstack(
                rx.heading("Projects", size="8"),
                create_project_dialog(),
                justify="between",
                align="center",
                width="100%",
                margin_bottom="1rem"
            ),

            # Error message display
            rx.cond(
                ProjectListState.error_message != "",
                rx.callout(
                    ProjectListState.error_message,
                    icon="triangle_alert",
                    color_scheme="red",
                    role="alert",
                    margin_bottom="1rem"
                ),
            ),

            # Loading indicator
            rx.cond(
                ProjectListState.is_loading,
                rx.center(
                    rx.spinner(size="3"),
                    padding="2rem"
                ),
                # Project table
                rx.cond(
                    ProjectListState.projects.length() > 0,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Title"),
                                rx.table.column_header_cell("Description"),
                                rx.table.column_header_cell("Start Date"),
                                rx.table.column_header_cell("End Date"),
                                rx.table.column_header_cell("Project Manager"),
                                rx.table.column_header_cell("Created By"),
                                rx.table.column_header_cell("Created At"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                ProjectListState.projects,
                                _row
                            )
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    # Empty state when no projects
                    rx.center(
                        rx.vstack(
                            rx.icon("folder_open", size=48, color="gray"),
                            rx.text(
                                "No projects found",
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
            ),

            width="100%",
            spacing="4",
            padding="2rem"
        )
    )


def _row(project: ProjectDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.link(
                project.title,
                href=f"/project/{project.id}",
                color="blue",
                text_decoration="underline",
                cursor="pointer"
            )
        ),
        rx.table.cell(
            rx.text(
                project.description,
                max_width="300px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap"
            )
        ),
        rx.table.cell(project.start_date),
        rx.table.cell(project.end_date),
        rx.table.cell(user_inline_component(project.project_manager)),
        rx.table.cell(user_inline_component(project.created_by)),
        rx.table.cell(rx.moment(project.created_at, format="MMM D, YYYY")),
    )
