import reflex as rx
from gws_reflex_main import (
    main_component,
    right_sidebar_close_button,
    translate,
)

from ..common.breadcrumb.breadcrumb_component import breadcrumb_component
from ..common.breadcrumb.breadcrumb_state import BreadcrumbState
from ..common.detail_page_layout import detail_page_layout
from ..common.details_sidebar.details_sidebar_parts import sidebar_section_label
from ..common.details_sidebar.project_details_sections import project_details_sections
from ..common.documents_list.documents_list_component import documents_list_content
from ..common.documents_list.documents_list_state import DocumentsListState
from ..common.page_layout import page_layout
from ..common.projects.project_access_component import project_access_error_component
from ..common.projects.project_page_state import ProjectPageState
from ..common.projects.project_status_chip_component import project_status_chip
from ..move_task_dialog.move_task_dialog_component import move_task_dialog
from ..project_form_dialog.project_form_dialog_component import project_update_dialog
from ..project_form_dialog.project_form_dialog_state import ProjectFormDialogState
from ..task_form.task_form_dialog_component import task_form_dialog
from ..task_list.task_list_component import task_list_content
from . import project_detail_translations  # noqa: F401  (side effect: registers translations)
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
                translate("project_detail.create_task"),
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
                    translate("project_detail.view"),
                    translate("project_detail.edit"),
                ),
                variant="solid",
                size="2",
                on_click=ProjectDetailState.toggle_description_edit_mode,
            ),
        ),
        (
            "documents",
            rx.hstack(
                rx.button(
                    rx.icon("file-plus", size=16),
                    translate("project_detail.create_note"),
                    variant="soft",
                    size="2",
                    on_click=DocumentsListState.open_create_note_dialog,
                ),
                rx.upload.root(
                    rx.button(
                        rx.spinner(loading=DocumentsListState.is_uploading),
                        rx.icon("upload", size=16),
                        translate("project_detail.upload_file"),
                        variant="solid",
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
                spacing="2",
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
                translate("project_detail.update_project"),
                on_click=lambda: ProjectFormDialogState.open_update_dialog(
                    ProjectDetailState.project
                ),
            ),
            rx.menu.item(
                rx.icon("users", size=16),
                translate("project_detail.manage_users"),
                on_click=ManageUsersDialogState.open_dialog,
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash-2", size=16),
                translate("project_detail.delete_project"),
                color_scheme="red",
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


def _tab_count_badge(count: rx.Var[int]) -> rx.Component:
    """Create a small count badge for a tab title.

    :param count: The count value to display
    :type count: rx.Var[int]
    :return: The styled count badge component
    :rtype: rx.Component
    """
    return rx.badge(
        count,
        variant="soft",
        size="1",
        radius="full",
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
                rx.tabs.trigger(
                    rx.hstack(
                        rx.text(translate("project_detail.tasks_tab")),
                        rx.cond(
                            ProjectDetailState.children_count,
                            _tab_count_badge(ProjectDetailState.children_count.subtask_count),
                        ),
                        align="center",
                        spacing="2",
                    ),
                    value="list",
                ),
                rx.tabs.trigger(
                    rx.text(translate("project_detail.description_tab")),
                    value="description",
                ),
                rx.tabs.trigger(
                    rx.hstack(
                        rx.text(translate("project_detail.documents_tab")),
                        rx.cond(
                            ProjectDetailState.children_count,
                            _tab_count_badge(ProjectDetailState.children_count.document_count),
                        ),
                        align="center",
                        spacing="2",
                    ),
                    value="documents",
                ),
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
            flex="1",
            min_height="0",
            display="flex",
            flex_direction="column",
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
        display="flex",
        flex_direction="column",
        class_name="project-main-content-area",
    )


def details_sidebar() -> rx.Component:
    """Create the details sidebar (right side) with project information.

    The sections themselves are shared with the details panel opened from the Gantt
    (see `common/details_sidebar/`), so both read the same; only the heading row differs.

    :return: The details sidebar component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Heading with close button
        rx.hstack(
            sidebar_section_label(translate("details_sidebar.project.title")),
            rx.spacer(),
            right_sidebar_close_button(),
            width="100%",
            align="center",
        ),
        project_details_sections(
            project=ProjectDetailState.project,
            project_users=ProjectDetailState.project_users,
            created_at_text=ProjectDetailState.created_at_text,
            last_modified_at_text=ProjectDetailState.last_modified_at_text,
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
        rx.cond(
            # A project id in the URL may not exist, or may belong to a project the
            # user is not a member of: say so instead of rendering an empty page.
            ProjectPageState.access_error != "",
            page_layout(project_access_error_component()),
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
                max_content_width="1200px",
                height="100vh",
                padding="0",
            ),
        ),
        # Add the update dialog
        project_update_dialog(),
        # Add the manage users dialog
        manage_users_dialog(),
        # Add the task form dialog
        task_form_dialog(),
        # Add the move task dialog
        move_task_dialog(),
    )
