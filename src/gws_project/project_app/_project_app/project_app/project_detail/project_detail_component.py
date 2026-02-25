import reflex as rx
from gws_reflex_main import (
    main_component,
    right_sidebar_close_button,
    right_sidebar_open_button,
    user_inline_component,
)

from ..common.breadcrumb.breadcrumb_component import breadcrumb_component
from ..common.breadcrumb.breadcrumb_state import BreadcrumbState
from ..common.detail_page_layout import detail_page_layout
from ..common.documents_list.documents_list_component import documents_list_content
from ..common.documents_list.documents_list_state import DocumentsListState
from ..common.page_layout import page_layout
from ..common.progress_ring import progress_ring
from ..common.tasks.project_status_chip_component import project_status_chip
from ..project_form_dialog.project_form_dialog_component import project_update_dialog
from ..project_form_dialog.project_form_dialog_state import ProjectFormDialogState
from ..task_form.task_form_dialog_component import task_form_dialog
from ..task_list.task_list_component import task_list_content
from .manage_users_dialog_component import ManageUsersDialogState, manage_users_dialog
from .project_description_component import project_description_content
from .project_detail_state import ProjectDetailState


def _tab_action_button() -> rx.Component:
    """Create the action button that changes based on the active tab.

    - Tasks tab: "Create Task" button
    - Description tab: "Edit"/"View" toggle button
    - Documents tab: "Upload File" button

    :return: The conditional action button component
    :rtype: rx.Component
    """
    return rx.match(
        ProjectDetailState.view_mode,
        (
            "list",
            rx.button(
                rx.icon("plus", size=16),
                "Create Task",
                variant="solid",
                size="2",
                on_click=ProjectDetailState.open_create_task_dialog,
            ),
        ),
        (
            "description",
            rx.button(
                rx.icon(
                    rx.cond(
                        ProjectDetailState.description_edit_mode,
                        "eye",
                        "pencil",
                    ),
                    size=16,
                ),
                rx.cond(
                    ProjectDetailState.description_edit_mode,
                    "View",
                    "Edit",
                ),
                variant="soft",
                size="2",
                on_click=ProjectDetailState.toggle_description_edit_mode,
            ),
        ),
        (
            "documents",
            rx.upload.root(
                rx.button(
                    rx.spinner(loading=DocumentsListState.is_uploading),
                    rx.icon("upload", size=16),
                    "Upload File",
                    variant="soft",
                    size="2",
                ),
                id="document_upload",
                multiple=True,
                on_drop=DocumentsListState.handle_upload(
                    rx.upload_files(
                        "document_upload",
                        on_upload_progress=DocumentsListState.handle_upload_progress,
                    )
                ),
            ),
        ),
        rx.fragment(),
    )


def project_action_menu() -> rx.Component:
    """Create the project action menu with update, manage users, and delete options.

    :return: The action menu component
    :rtype: rx.Component
    """
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(rx.icon("ellipsis-vertical", size=18), variant="ghost", color_scheme="gray")
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("pencil", size=16),
                "Update Project",
                on_click=lambda: ProjectFormDialogState.open_update_dialog(
                    ProjectDetailState.project
                ),
            ),
            rx.menu.item(
                rx.icon("users", size=16),
                "Manage Users",
                on_click=ManageUsersDialogState.open_dialog,
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash-2", size=16),
                "Delete Project",
                color="red",
                on_click=ProjectDetailState.open_delete_project_dialog,
            ),
        ),
    )


def header() -> rx.Component:
    """Create the header component for the project detail page.

    :return: The header component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Title
        rx.heading(
            ProjectDetailState.project.title,
            size="6",
        ),
        rx.box(
            project_status_chip(
                ProjectDetailState.project.status,
            ),
            margin_left="0.5rem",
        ),
        rx.spacer(),
        # Action menu
        project_action_menu(),
        width="100%",
        align="center",
        spacing="2",
    )


def main_content_area() -> rx.Component:
    """Create the main content area with tabs for switching between views.

    The tab bar includes the view triggers on the left and a contextual
    action button on the right (e.g. "Create Task", "Edit"/"View", "Upload File").

    :return: The main content area component
    :rtype: rx.Component
    """
    return rx.tabs.root(
        # Tab bar row: triggers on the left, action button on the right
        rx.hstack(
            rx.tabs.list(
                rx.tabs.trigger("Tasks", value="list"),
                rx.tabs.trigger("Description", value="description"),
                rx.tabs.trigger("Documents", value="documents"),
            ),
            rx.spacer(),
            _tab_action_button(),
            width="100%",
            align="center",
        ),
        # Tab content panels
        rx.tabs.content(
            task_list_content(),
            value="list",
            padding_top="1rem",
        ),
        rx.tabs.content(
            project_description_content(),
            value="description",
            padding_top="1rem",
        ),
        rx.tabs.content(
            documents_list_content(),
            value="documents",
            padding_top="1rem",
        ),
        value=ProjectDetailState.view_mode,
        on_change=ProjectDetailState.set_view_mode,
        width="100%",
        # full height but not overflow parent
        flex="1",
        min_height="0",
        class_name="project-main-content-area",
    )


def _sidebar_section_label(label: str) -> rx.Component:
    """Create a small uppercase gray label for a sidebar section.

    :param label: The label text
    :type label: str
    :return: The styled label component
    :rtype: rx.Component
    """
    return rx.text(
        label,
        size="1",
        color="gray",
        weight="bold",
        style={
            "text-transform": "uppercase",
            "letter-spacing": "0.06em",
        },
    )


def _sidebar_metadata_row(label: str, value: rx.Component) -> rx.Component:
    """Create a metadata row with a label on the left and value on the right.

    :param label: The label text
    :type label: str
    :param value: The value component
    :type value: rx.Component
    :return: The metadata row component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.text(label, size="2", color="gray"),
        rx.spacer(),
        value,
        width="100%",
        align="center",
    )


def details_sidebar() -> rx.Component:
    """Create the details sidebar (right side) with project information.

    Layout follows the visual structure from example.jsx:
    - Heading
    - Centered progress ring
    - Manager section
    - Period section with styled date box
    - Members list
    - Metadata section with divider

    :return: The details sidebar component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Heading with close button
        rx.hstack(
            _sidebar_section_label("Project details"),
            rx.spacer(),
            right_sidebar_close_button(),
            width="100%",
            align="center",
        ),
        # Centered progress ring
        rx.flex(
            progress_ring(ProjectDetailState.project.progress, size="big"),
            justify="center",
            width="100%",
            margin_bottom="0.5rem",
        ),
        # Manager section
        rx.vstack(
            _sidebar_section_label("Manager"),
            user_inline_component(ProjectDetailState.project.project_manager),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Period section
        rx.vstack(
            _sidebar_section_label("Period"),
            rx.hstack(
                rx.text(
                    rx.moment(ProjectDetailState.project.start_date, format="MMM D, YYYY"),
                    size="2",
                    weight="bold",
                    color="var(--accent-9)",
                ),
                rx.text("→", size="2", color="gray"),
                rx.text(
                    rx.moment(ProjectDetailState.project.end_date, format="MMM D, YYYY"),
                    size="2",
                    weight="bold",
                    color="var(--accent-9)",
                ),
                background="var(--accent-2)",
                border_radius="12px",
                padding="12px 14px",
                align="center",
                spacing="3",
                width="100%",
            ),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Members section
        rx.vstack(
            _sidebar_section_label("Members"),
            rx.cond(
                ProjectDetailState.project_users.length() > 0,
                rx.vstack(
                    rx.foreach(
                        ProjectDetailState.project_users,
                        lambda project_user: user_inline_component(project_user.user),
                    ),
                    spacing="2",
                    align_items="start",
                    width="100%",
                ),
                rx.text("No team members", size="2", color="gray"),
            ),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Divider + metadata section
        rx.vstack(
            rx.divider(),
            _sidebar_metadata_row(
                "Created by",
                user_inline_component(ProjectDetailState.project.created_by, size="small"),
            ),
            _sidebar_metadata_row(
                "Created at",
                rx.text(
                    rx.moment(ProjectDetailState.project.created_at, format="MMM D, YYYY HH:mm"),
                    size="1",
                    weight="medium",
                ),
            ),
            _sidebar_metadata_row(
                "Last modified by",
                user_inline_component(ProjectDetailState.project.last_modified_by, size="small"),
            ),
            _sidebar_metadata_row(
                "Last modified at",
                rx.text(
                    rx.moment(
                        ProjectDetailState.project.last_modified_at, format="MMM D, YYYY HH:mm"
                    ),
                    size="1",
                    weight="medium",
                ),
            ),
            spacing="1",
            width="100%",
            padding_top="0.5rem",
        ),
        width="100%",
        spacing="5",
        align_items="start",
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
            # Project details with breadcrumb and header
            rx.cond(
                ProjectDetailState.project,
                detail_page_layout(
                    main_content=main_content_area(),
                    header_content=header(),
                ),
            ),
            # Right sidebar with project details
            right_sidebar_content=details_sidebar(),
            header_content=breadcrumb_component(BreadcrumbState.breadcrumbs),
            height="100vh",
            padding="0",
        ),
        # Add the update dialog
        project_update_dialog(),
        # Add the manage users dialog
        manage_users_dialog(),
        # Add the task form dialog
        task_form_dialog(),
    )
