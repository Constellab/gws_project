import reflex as rx
from gws_project.project.project_dto import ProjectUserDTO
from gws_reflex_main import confirm_dialog, user_inline_component

from .manage_users_dialog_state import (ManageUsersDialogState,
                                        RemoveUserDialogState)
from .project_detail_state import ProjectDetailState
from .project_user_form_dialog_component import project_user_form_dialog
from .project_user_form_dialog_state import ProjectUserFormDialogState


def user_action_menu(project_user: ProjectUserDTO) -> rx.Component:
    """Create the action menu for a project user.

    Provides options to update the user's role or remove them from the project.

    :param project_user: The project user data transfer object
    :type project_user: ProjectUserDTO
    :return: The action menu component
    :rtype: rx.Component
    """
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("ellipsis-vertical", size=16),
                variant="ghost",
                size="1",
            )
        ),
        rx.menu.content(
            rx.menu.item(
                "Update Role",
                on_click=ProjectUserFormDialogState.open_update_dialog(project_user)
            ),
            rx.menu.separator(),
            rx.menu.item(
                "Remove from Project",
                color="red",
                on_click=RemoveUserDialogState.open_user_dialog(project_user)
            ),
        ),
    )


def user_table_row(project_user: ProjectUserDTO) -> rx.Component:
    """Create a table row for a project user.

    Displays the user information, role, and action menu.

    :param project_user: The project user data transfer object
    :type project_user: ProjectUserDTO
    :return: The table row component
    :rtype: rx.Component
    """
    return rx.table.row(
        rx.table.cell(
            user_inline_component(project_user.user),
            vertical_align="middle"
        ),
        rx.table.cell(
            rx.badge(
                project_user.role,
                color_scheme=rx.cond(
                    project_user.role == "OWNER",
                    "blue",
                    rx.cond(
                        project_user.role == "USER",
                        "green",
                        "gray"
                    )
                )
            ),
            vertical_align="middle"
        ),
        rx.table.cell(
            user_action_menu(project_user),
            align="right",
            vertical_align="middle"
        ),
    )


def users_table() -> rx.Component:
    """Create the table displaying all project users.

    Shows user information, roles, and action buttons in a responsive table.

    :return: The users table component
    :rtype: rx.Component
    """
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("User"),
                rx.table.column_header_cell("Role"),
                rx.table.column_header_cell("Actions", align="right"),
            )
        ),
        rx.table.body(
            rx.foreach(
                ProjectDetailState.project_users,
                user_table_row
            )
        ),
        width="100%",
        variant="surface",
    )


def manage_users_dialog() -> rx.Component:
    """Create the manage users dialog component.

    Displays a dialog with a table of all project users, their roles,
    and action buttons for managing users. The dialog can be opened
    by clicking the "Manage Users" button in the project detail page.

    Includes a nested form dialog for adding/updating users and a confirmation
    dialog for removing users.

    :return: The manage users dialog component
    :rtype: rx.Component
    """
    return rx.fragment(
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.hstack(
                        rx.text("Manage Team Members", flex=1),
                        rx.button(
                            rx.icon("user-plus", size=18),
                            "Add User",
                            size="2",
                            on_click=ProjectUserFormDialogState.open_create_dialog,
                        ),
                    ),
                ),
                rx.dialog.description(
                    "View and manage users for this project.",
                    size="2",
                    margin_bottom="1rem",
                ),
                # Users table
                rx.cond(
                    ProjectDetailState.project_users.length() > 0,
                    users_table(),
                    rx.text(
                        "No team members found.",
                        size="2",
                        color="gray",
                        align="center",
                        padding="2rem"
                    )
                ),
                # Close button
                rx.flex(
                    rx.dialog.close(
                        rx.button(
                            "Close",
                            variant="soft",
                            on_click=ManageUsersDialogState.close_dialog,
                        ),
                    ),
                    justify="end",
                    margin_top="1rem",
                ),
                max_width="600px",
            ),
            open=ManageUsersDialogState.dialog_opened,
        ),
        # Nested form dialog for adding/updating users
        project_user_form_dialog(),

        # Confirmation dialog for removing users
        confirm_dialog(
            title="Remove User from Project",
            content="Are you sure you want to remove " +
            RemoveUserDialogState.user_to_remove.user.first_name + " " + RemoveUserDialogState.user_to_remove.user.last_name +
            " from this project?",
            state=RemoveUserDialogState,
        )
    )
