import reflex as rx
from gws_reflex_main import (
    main_component,
    right_sidebar_close_button,
    translate,
)
from gws_reflex_main.gws_components import rich_text_component

from ..common.breadcrumb.breadcrumb_component import breadcrumb_component
from ..common.breadcrumb.breadcrumb_state import BreadcrumbState
from ..common.detail_page_layout import detail_page_layout
from ..common.details_sidebar.details_sidebar_parts import sidebar_section_label
from ..common.details_sidebar.task_details_sections import task_details_sections
from ..common.documents_list.documents_list_component import documents_list_content
from ..common.documents_list.documents_list_state import DocumentsListState
from ..common.page_layout import page_layout
from ..common.projects.project_access_component import project_access_error_component
from ..common.projects.project_page_state import ProjectPageState
from ..common.tasks.task_actions_menu import task_actions_menu
from ..common.tasks.task_components import task_icon_component
from ..common.tasks.task_priority_chip_component import task_priority_chip
from ..common.tasks.task_status_chip_component import task_status_chip
from ..move_task_dialog.move_task_dialog_component import move_task_dialog
from ..task_activity.task_activity_component import task_activity_content
from ..task_activity.task_activity_state import TaskActivityState
from ..task_form.task_form_dialog_component import task_form_dialog
from ..task_list.task_list_component import task_list_content
from . import task_detail_translations  # noqa: F401  (side effect: registers translations)
from .task_detail_state import TaskDetailState


def _tab_action_button() -> rx.Component:
    """Create the action button that changes based on the active tab.

    - Subtasks tab: "Create Subtask" button
    - Description tab: "Edit"/"View" toggle button
    - Documents tab: "Upload File" button

    :return: The conditional action button component
    :rtype: rx.Component
    """
    return rx.match(
        TaskDetailState.view_mode,
        (
            "list",
            rx.button(
                rx.icon("plus", size=16),
                translate("task_detail.tab_action.create_subtask"),
                variant="solid",
                size="2",
                on_click=TaskDetailState.open_create_subtask_dialog,
            ),
        ),
        (
            "description",
            rx.button(
                rx.icon(
                    rx.cond(
                        TaskDetailState.description_edit_mode,
                        "eye",
                        "pencil",
                    ),
                    size=16,
                ),
                rx.cond(
                    TaskDetailState.description_edit_mode,
                    translate("task_detail.tab_action.view"),
                    translate("task_detail.tab_action.edit"),
                ),
                variant="solid",
                size="2",
                on_click=TaskDetailState.toggle_description_edit_mode,
            ),
        ),
        (
            "documents",
            rx.hstack(
                rx.button(
                    rx.icon("file-plus", size=16),
                    translate("task_detail.tab_action.create_note"),
                    variant="soft",
                    size="2",
                    on_click=DocumentsListState.open_create_note_dialog,
                ),
                rx.upload.root(
                    rx.button(
                        rx.spinner(loading=DocumentsListState.is_uploading),
                        rx.icon("upload", size=16),
                        translate("task_detail.tab_action.upload_file"),
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


def task_header() -> rx.Component:
    """Create the task header with icon, title, status, and action menu.

    :return: The task header component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Icon indicating if task allows subtasks
        task_icon_component(TaskDetailState.task, size="6"),
        # Title
        rx.heading(
            TaskDetailState.task.title,
            size="6",
        ),
        # Status and priority badges beside title
        rx.hstack(
            task_status_chip(
                TaskDetailState.task.status,
                on_status_change=TaskDetailState.update_status,
                allow_subtask=TaskDetailState.task.allow_subtasks,
            ),
            task_priority_chip(
                TaskDetailState.task.priority,
                on_priority_change=TaskDetailState.update_priority,
                allow_subtask=TaskDetailState.task.allow_subtasks,
            ),
            spacing="2",
            align="center",
            margin_left="0.5rem",
        ),
        rx.spacer(),
        # Action menu (Update, Change Type, and Delete)
        task_actions_menu(
            on_update=TaskDetailState.open_update_task_dialog,
            on_delete=TaskDetailState.open_delete_task_dialog,
            on_change_type=TaskDetailState.open_change_task_type_dialog,
            on_move=TaskDetailState.open_move_task_dialog,
        ),
        width="100%",
        align="center",
        spacing="2",
    )


def _task_description_content() -> rx.Component:
    """Create the description content without header.

    The header (title and action button) is managed at the tab level.

    :return: The description content component
    :rtype: rx.Component
    """
    return rx.vstack(
        rich_text_component(
            value=TaskDetailState.task.description,
            disabled=~TaskDetailState.description_edit_mode,
            output_event=TaskDetailState.handle_description_change,
            custom_style=rx.cond(
                TaskDetailState.description_edit_mode,
                {"flex": "1", "display": "flex", "backgroundColor": "var(--card-background)"},
                {
                    "padding": "0",
                    "flex": "1",
                    "display": "flex",
                    "backgroundColor": "var(--card-background)",
                },
            ),
        ),
        width="100%",
        spacing="3",
        align_items="start",
        flex="1",
        min_height="0",
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
    action button on the right. The Subtasks tab is only shown if the task
    allows subtasks.

    :return: The main content area component
    :rtype: rx.Component
    """
    return rx.tabs.root(
        # Tab bar row: triggers on the left, action button on the right
        rx.hstack(
            rx.tabs.list(
                # Subtasks tab - only shown if task allows subtasks
                rx.cond(
                    TaskDetailState.task.allow_subtasks,
                    rx.tabs.trigger(
                        rx.hstack(
                            rx.text(translate("task_detail.tab.subtasks")),
                            rx.cond(
                                TaskDetailState.children_count,
                                _tab_count_badge(TaskDetailState.children_count.subtask_count),
                            ),
                            align="center",
                            spacing="2",
                        ),
                        value="list",
                    ),
                ),
                rx.tabs.trigger(
                    rx.text(translate("task_detail.tab.description")),
                    value="description",
                ),
                rx.tabs.trigger(
                    rx.hstack(
                        rx.text(translate("task_detail.tab.documents")),
                        rx.cond(
                            TaskDetailState.children_count,
                            _tab_count_badge(TaskDetailState.children_count.document_count),
                        ),
                        align="center",
                        spacing="2",
                    ),
                    value="documents",
                ),
                rx.tabs.trigger(
                    rx.hstack(
                        rx.text(translate("task_detail.tab.activity")),
                        rx.cond(
                            TaskActivityState.activity_items.length() > 0,
                            _tab_count_badge(TaskActivityState.activity_items.length()),
                        ),
                        align="center",
                        spacing="2",
                    ),
                    value="activity",
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
            _task_description_content(),
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
        rx.tabs.content(
            task_activity_content(),
            value="activity",
            padding_top="1rem",
        ),
        value=TaskDetailState.view_mode,
        on_change=TaskDetailState.set_view_mode,
        width="100%",
        flex="1",
        min_height="0",
        display="flex",
        flex_direction="column",
    )


def details_sidebar() -> rx.Component:
    """Create the details sidebar (right side) with task information.

    The sections themselves are shared with the details panel opened from Kanban,
    Gantt, Planning and My work (see `common/details_sidebar/`), so both read the same;
    only the heading row differs.

    :return: The details sidebar component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Heading with close button
        rx.hstack(
            sidebar_section_label(translate("details_sidebar.task.title")),
            rx.spacer(),
            right_sidebar_close_button(),
            width="100%",
            align="center",
        ),
        task_details_sections(
            task=TaskDetailState.task,
            created_at_text=TaskDetailState.created_at_text,
            last_modified_at_text=TaskDetailState.last_modified_at_text,
            parent_task=TaskDetailState.parent_task,
            subtask_members=TaskDetailState.subtask_members,
            on_status_change=TaskDetailState.update_status,
            on_priority_change=TaskDetailState.update_priority,
        ),
        width="100%",
        spacing="5",
        align_items="start",
    )


def task_detail_page() -> rx.Component:
    """Create the task detail page component.

    This component displays all details of a single task using a Jira-like layout
    with main content on the left and a details sidebar on the right.

    :return: The task detail page component
    :rtype: rx.Component
    """
    return main_component(
        rx.cond(
            # A task id in the URL may not exist, or may belong to a project the
            # user is not a member of: say so instead of rendering an empty page.
            ProjectPageState.access_error != "",
            page_layout(project_access_error_component()),
            page_layout(
                rx.cond(
                    TaskDetailState.task,
                    detail_page_layout(
                        main_content=main_content_area(),
                        header_content=task_header(),
                    ),
                ),
                right_sidebar_content=details_sidebar(),
                header_content=breadcrumb_component(BreadcrumbState.breadcrumbs),
                max_content_width="1200px",
                height="100vh",
                padding="0",
            ),
        ),
        # Add the task form dialog
        task_form_dialog(),
        # Add the move task dialog
        move_task_dialog(),
    )
