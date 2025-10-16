
import reflex as rx
from gws_project.project.project_dto import ProjectDTO
from gws_reflex_main import main_component, user_inline_component

from ..create_project_dialog.project_form_dialog_component import \
    project_update_dialog
from ..create_project_dialog.project_form_dialog_state import \
    ProjectFormDialogState
from .project_detail_state import ProjectDetailState


def header(project: ProjectDTO) -> rx.Component:
    """Create the header component for the project detail page.

    This component displays the project title, dates, and project manager.

    :param project: The project data transfer object
    :type project: ProjectDTO
    :return: The header component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Title
        rx.heading(
            project.title,
            size="8",
            margin_bottom="0.5rem"
        ),
        # Calendar icon with dates
        rx.icon("calendar", size=18),
        rx.text(
            rx.moment(
                project.start_date,
                format="MMM D, YYYY"
            ),
            " - ",
            rx.moment(
                project.end_date,
                format="MMM D, YYYY"
            ),
            size="3",
            color="gray"
        ),
        # Project Manager
        user_inline_component(project.project_manager),
        spacing="2",
        align="center",
    )

def project_detail_page() -> rx.Component:
    """Create the project detail page component.

    This component displays all details of a single project including
    title, description, dates, project manager, and creator information.

    :return: The project detail page component
    :rtype: rx.Component
    """
    return main_component(
        rx.vstack(
            # Header with back button and update button
            rx.hstack(
                rx.link(
                    rx.button(
                        rx.icon("arrow_left", size=18),
                        "Back to Projects",
                        variant="soft",
                    ),
                    href="/",
                ),
                rx.spacer(),
                rx.cond(
                    ProjectDetailState.project,
                    rx.button(
                        rx.icon("pencil", size=18),
                        "Update Project",
                        on_click=lambda: ProjectFormDialogState.open_update_dialog(ProjectDetailState.project)
                    ),
                ),
                justify="between",
                align="center",
                width="100%",
                margin_bottom="1rem"
            ),

            # Error message display
            rx.cond(
                ProjectDetailState.error_message != "",
                rx.callout(
                    ProjectDetailState.error_message,
                    icon="triangle_alert",
                    color_scheme="red",
                    role="alert",
                    margin_bottom="1rem"
                ),
            ),

            # Loading indicator
            rx.cond(
                ProjectDetailState.is_loading,
                rx.center(
                    rx.spinner(size="3"),
                    padding="2rem"
                ),
                # Project details
                rx.cond(
                    ProjectDetailState.project,
                    rx.vstack(
                        # Header with title, dates, and project manager
                        header(ProjectDetailState.project),
                        # Description (without label)
                        rx.text(
                            ProjectDetailState.project.description,
                            size="3",
                            color="gray",
                            margin_top="0.5rem"
                        ),

                        width="100%",
                        spacing="4"
                    ),
                )
            ),

            width="100%",
            spacing="4",
            padding="2rem"
        ),
        # Add the update dialog
        project_update_dialog()
    )
