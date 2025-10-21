
import reflex as rx
from gws_project.project.project_dto import ProjectUserDTO
from gws_reflex_main import (main_component, user_inline_component,
                             user_profile_picture)

from ..common.detail_page_layout import detail_page_layout
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


def project_user_item(project_user: ProjectUserDTO) -> rx.Component:
    """Create a project user item component displaying user photo and role.

    :param project_user: The project user data transfer object
    :type project_user: ProjectUserDTO
    :return: The project user item component
    :rtype: rx.Component
    """
    return user_profile_picture(project_user.user, size="40px")


def main_content_area() -> rx.Component:
    """Create the main content area (left side) with title, description, team members, and tasks.

    :return: The main content area component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Title row with action menu
        rx.hstack(
            # Title
            rx.heading(
                ProjectDetailState.project.title,
                size="8",
            ),
            rx.spacer(),
            # Action menu
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.icon("ellipsis-vertical", size=18),
                        variant="soft",
                        color_scheme="gray"
                    )
                ),
                rx.menu.content(
                    rx.menu.item(
                        rx.icon("pencil", size=16),
                        "Update Project",
                        on_click=lambda: ProjectFormDialogState.open_update_dialog(ProjectDetailState.project)
                    ),
                    rx.menu.item(
                        rx.icon("users", size=16),
                        "Manage Users",
                        on_click=ManageUsersDialogState.open_dialog
                    ),
                    rx.menu.separator(),
                    rx.menu.item(
                        rx.icon("trash_2", size=16),
                        "Delete Project",
                        color="red",
                        on_click=lambda: DeleteProjectDialogState.open_dialog_with_project(
                            ProjectDetailState.project.id)
                    ),
                ),
            ),
            width="100%",
            align="center",
            spacing="2"
        ),

        # Description section
        rx.vstack(
            rx.heading("Description", size="4", weight="bold", margin_top="1.5rem"),
            rx.text(
                ProjectDetailState.project.description,
                size="3",
                color="gray",
                white_space="pre-wrap"
            ),
            width="100%",
            spacing="2",
            align_items="start"
        ),

        # Tasks section
        rx.vstack(
            # Header with title, view toggle, and create button
            rx.hstack(
                rx.heading(
                    "Tasks",
                    size="4",
                    weight="bold",
                    margin_top="1.5rem"
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
                    size="2",
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
        ),

        width="100%",
        spacing="3",
        align_items="start",
        flex="1"
    )


def details_sidebar() -> rx.Component:
    """Create the details sidebar (right side) with technical information.

    :return: The details sidebar component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.heading("Details", size="5", margin_bottom="1rem"),

        # Details grid - single parent grid with all fields
        rx.grid(
            # Project Manager
            rx.text("Project Manager", size="2", color="gray", weight="medium"),
            user_inline_component(ProjectDetailState.project.project_manager),

            # Start date
            rx.text("Start date", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(ProjectDetailState.project.start_date, format="MMM D, YYYY"),
                size="2"
            ),

            # End date
            rx.text("End date", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(ProjectDetailState.project.end_date, format="MMM D, YYYY"),
                size="2"
            ),

            # Project members
            rx.text("Project Members", size="2", color="gray", weight="medium"),
            rx.cond(
                ProjectDetailState.project_users.length() > 0,
                rx.vstack(
                    rx.foreach(
                        ProjectDetailState.project_users,
                        lambda project_user: user_inline_component(project_user.user),
                    ),
                    spacing="2",
                    align_items="start",
                    width="100%"
                ),
                rx.text("No team members", size="2", color="gray")
            ),

            # Divider before technical info (spans 2 columns)
            rx.divider(margin_top="0.5rem", margin_bottom="0.5rem", grid_column="span 2"),

            # Created by
            rx.text("Created by", size="2", color="gray", weight="medium"),
            user_inline_component(ProjectDetailState.project.created_by),

            # Created at
            rx.text("Created at", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(ProjectDetailState.project.created_at, format="MMM D, YYYY HH:mm"),
                size="2",
            ),

            # Last modified by
            rx.text("Last modified by", size="2", color="gray", weight="medium"),
            user_inline_component(ProjectDetailState.project.last_modified_by),

            # Last modified at
            rx.text("Last modified at", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(ProjectDetailState.project.last_modified_at, format="MMM D, YYYY HH:mm"),
                size="2",
            ),

            columns="2",
            spacing="3",
            width="100%",
            row_gap="1rem"
        ),

        width="100%",
        spacing="3",
        align_items="start"
    )


def project_detail_page() -> rx.Component:
    """Create the project detail page component.

    This component displays all details of a single project using a Jira-like layout
    with main content on the left and a details sidebar on the right.

    :return: The project detail page component
    :rtype: rx.Component
    """
    return main_component(
        rx.vstack(
            # Project details in two-column layout with breadcrumb
            rx.cond(
                ProjectDetailState.project,
                detail_page_layout(
                    main_content=main_content_area(),
                    sidebar_content=details_sidebar()
                ),
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
