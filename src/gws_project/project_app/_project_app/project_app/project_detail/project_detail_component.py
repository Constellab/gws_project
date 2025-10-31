
import reflex as rx
from gws_reflex_main import main_component, user_inline_component

from ..common.breadcrumb.breadcrumb_state import BreadcrumbState
from ..common.detail_page_layout import detail_page_layout
from ..common.documents_list.documents_list_component import \
    documents_list_view
from ..common.page_layout import page_layout
from ..project_form_dialog.project_form_dialog_component import \
    project_update_dialog
from ..project_form_dialog.project_form_dialog_state import \
    ProjectFormDialogState
from ..task_form.task_form_dialog_component import task_form_dialog
from ..task_list.task_kanban_component import task_kanban_view
from ..task_list.task_list_component import task_list_view
from .manage_users_dialog_component import (ManageUsersDialogState,
                                            manage_users_dialog)
from .project_description_component import project_description_component
from .project_detail_state import ProjectDetailState


def view_mode_segmented_control() -> rx.Component:
    """Create the view mode segmented control for switching between views.

    :return: The segmented control component
    :rtype: rx.Component
    """
    return rx.segmented_control.root(
        rx.segmented_control.item(
            rx.tooltip(
                rx.icon("file-text", size=16),
                content="View description"
            ),
            value="description",
        ),
        rx.segmented_control.item(
            rx.tooltip(
                rx.icon("folder-open", size=16),
                content="View documents"
            ),
            value="documents",
        ),
        rx.segmented_control.item(
            rx.tooltip(
                rx.icon("list", size=16),
                content="View tasks as list"
            ),
            value="list",
        ),
        rx.segmented_control.item(
            rx.tooltip(
                rx.icon("kanban", size=16),
                content="View tasks as kanban board"
            ),
            value="kanban",
        ),
        value=ProjectDetailState.view_mode,
        on_change=ProjectDetailState.set_view_mode,
        size="2",
    )


def project_action_menu() -> rx.Component:
    """Create the project action menu with update, manage users, and delete options.

    :return: The action menu component
    :rtype: rx.Component
    """
    return rx.menu.root(
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
                on_click=ProjectDetailState.open_delete_project_dialog
            ),
        ),
    )


def main_content_area() -> rx.Component:
    """Create the main content area (left side) with title, description, team members, and tasks.

    :return: The main content area component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Title row with segmented control and action menu
        rx.hstack(
            # Title
            rx.heading(
                ProjectDetailState.project.title,
                size="8",
            ),
            rx.spacer(),
            # View mode toggle buttons
            view_mode_segmented_control(),
            # Action menu
            project_action_menu(),
            width="100%",
            align="center",
            spacing="2"
        ),

        # Conditional rendering based on view mode
        rx.match(
            ProjectDetailState.view_mode,
            ("description", project_description_component()),
            ("documents", documents_list_view()),
            ("list", task_list_view()),
            ("kanban", task_kanban_view()),
            project_description_component(),  # default
        ),

        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
        class_name="project-main-content-area",
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
        page_layout(
            # Project details in two-column layout with breadcrumb
            rx.cond(
                ProjectDetailState.project,
                detail_page_layout(
                    main_content=main_content_area(),
                    sidebar_content=details_sidebar(),
                    breadcrumbs=BreadcrumbState.breadcrumbs
                ),
            ),
            height='100vh'
        ),
        # Add the update dialog
        project_update_dialog(),
        # Add the manage users dialog
        manage_users_dialog(),
        # Add the task form dialog
        task_form_dialog(),
    )
