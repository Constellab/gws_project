
import reflex as rx
from gws_project.project.project_dto import ProjectDTO, ProjectUserDTO
from gws_reflex_main import (main_component, user_inline_component,
                             user_profile_picture)

from ..create_project_dialog.project_form_dialog_component import \
    project_update_dialog
from ..create_project_dialog.project_form_dialog_state import \
    ProjectFormDialogState
from ..task_form.task_form_dialog_component import task_form_dialog
from ..task_form.task_form_dialog_state import TaskFormDialogState
from ..task_list.task_kanban_component import task_kanban_component
from ..task_list.task_list_component import task_list_component
from .delete_project_dialog_component import (DeleteProjectDialogState,
                                              delete_project_dialog)
from .manage_users_dialog_component import (ManageUsersDialogState,
                                            manage_users_dialog)
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


def project_user_item(project_user: ProjectUserDTO) -> rx.Component:
    """Create a project user item component displaying user photo and role.

    :param project_user: The project user data transfer object
    :type project_user: ProjectUserDTO
    :return: The project user item component
    :rtype: rx.Component
    """
    return user_profile_picture(project_user.user, size="40px")


def project_users_section() -> rx.Component:
    """Create the project users section displaying all users in a row.

    :return: The project users section component
    :rtype: rx.Component
    """
    return rx.cond(
        ProjectDetailState.project_users.length() > 0,
        rx.vstack(
            # Header with title and manage button
            rx.hstack(
                rx.heading(
                    "Team Members",
                    size="5",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("users", size=16),
                    "Manage Users",
                    variant="soft",
                    on_click=ManageUsersDialogState.open_dialog
                ),
                width="100%",
                align="center",
            ),
            # User avatars
            rx.hstack(
                rx.foreach(
                    ProjectDetailState.project_users,
                    project_user_item
                ),
                spacing="3",
                align="center",
            ),
            width="100%",
            spacing="3",
            align_items="start",
        )
    )


def tasks_section() -> rx.Component:
    """Create the tasks section with task list and create button.

    :return: The tasks section component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Header with title, view toggle, and create button
        rx.hstack(
            rx.heading(
                "Tasks",
                size="5",
            ),
            rx.spacer(),
            # View mode toggle buttons
            rx.segmented_control.root(
                rx.segmented_control.item(
                    rx.icon("list", size=16),
                    value="list",
                ),
                rx.segmented_control.item(
                    rx.icon("kanban", size=16),
                    value="kanban",
                ),
                value=ProjectDetailState.view_mode,
                on_change=ProjectDetailState.set_view_mode,
                size="2",
            ),
            rx.button(
                rx.icon("plus", size=16),
                "Create Root Task",
                variant="soft",
                on_click=lambda: TaskFormDialogState.open_create_dialog(ProjectDetailState.project)
            ),
            width="100%",
            align="center",
        ),
        # Conditional rendering based on view mode
        rx.cond(
            ProjectDetailState.view_mode == "list",
            task_list_component(),
            task_kanban_component()
        ),
        width="100%",
        spacing="3",
        align_items="start",
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
            # Header with back button and action buttons
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
                    rx.hstack(
                        rx.button(
                            rx.icon("pencil", size=18),
                            "Update Project",
                            on_click=lambda: ProjectFormDialogState.open_update_dialog(ProjectDetailState.project)
                        ),
                        rx.button(
                            rx.icon("trash_2", size=18),
                            "Delete",
                            color_scheme="red",
                            variant="soft",
                            on_click=lambda: DeleteProjectDialogState.open_dialog_with_project(
                                ProjectDetailState.project.id,
                            )
                        ),

                        spacing="2"
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
                        # Project users section
                        project_users_section(),

                        # Tasks section
                        tasks_section(),

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
        project_update_dialog(),
        # Add the delete confirmation dialog
        delete_project_dialog(),
        # Add the manage users dialog
        manage_users_dialog(),
        # Add the task form dialog
        task_form_dialog()
    )
