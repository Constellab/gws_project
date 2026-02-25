import reflex as rx
from gws_reflex_main import (
    main_component,
    right_sidebar_close_button,
    right_sidebar_open_button,
    user_inline_component,
)
from gws_reflex_main.gws_components import rich_text_component

from ...common.breadcrumb.breadcrumb_component import breadcrumb_component
from ...common.detail_page_layout import detail_page_layout
from ...common.page_layout import page_layout
from ...common.tasks.task_components import task_template_icon_component
from ...common.tasks.task_priority_chip_component import task_priority_chip
from ..task_template_form_dialog.task_template_form_dialog_component import (
    task_template_form_dialog,
)
from ..task_template_list.task_template_list_component import task_template_list_component
from ..task_template_list.task_template_list_state import TaskTemplateListState
from ..template_breadcrumb_state import TemplateBreadcrumbState
from .task_template_detail_state import TaskTemplateDetailState


def task_template_header() -> rx.Component:
    """Create the task template header with icon, title, and action menu.

    :return: The task template header component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Icon indicating if task template allows subtasks
        task_template_icon_component(TaskTemplateDetailState.task_template, size=24),
        # Title
        rx.heading(
            TaskTemplateDetailState.task_template.title,
            size="6",
        ),
        rx.spacer(),
        # Action menu (Update and Delete)
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.icon("ellipsis-vertical", size=18), variant="ghost", color_scheme="gray"
                )
            ),
            rx.menu.content(
                rx.menu.item(
                    rx.icon("pencil", size=16),
                    "Update Task Template",
                    on_click=TaskTemplateDetailState.open_update_task_template_dialog,
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.icon("trash-2", size=16),
                    "Delete",
                    color="red",
                    on_click=TaskTemplateDetailState.open_delete_task_template_dialog,
                ),
            ),
        ),
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


def _tab_action_button() -> rx.Component:
    """Create the action button that changes based on the active tab.

    - Subtasks tab: "Create Subtask Template" button (only if allows subtasks)
    - Description tab: "Edit"/"View" toggle button

    :return: The conditional action button component
    :rtype: rx.Component
    """
    return rx.match(
        TaskTemplateDetailState.view_mode,
        (
            "subtasks",
            rx.cond(
                TaskTemplateDetailState.task_template.allow_subtasks,
                rx.button(
                    rx.icon("plus", size=16),
                    "Create Subtask Template",
                    variant="solid",
                    size="2",
                    on_click=TaskTemplateDetailState.open_create_subtask_template_dialog,
                ),
                rx.fragment(),
            ),
        ),
        (
            "description",
            rx.button(
                rx.icon(
                    rx.cond(
                        TaskTemplateDetailState.description_edit_mode,
                        "eye",
                        "pencil",
                    ),
                    size=16,
                ),
                rx.cond(
                    TaskTemplateDetailState.description_edit_mode,
                    "View",
                    "Edit",
                ),
                variant="solid",
                size="2",
                on_click=TaskTemplateDetailState.toggle_description_edit_mode,
            ),
        ),
        rx.fragment(),
    )


def task_template_description() -> rx.Component:
    """Create the task template description section.

    :return: The task template description component
    :rtype: rx.Component
    """
    return rx.box(
        rich_text_component(
            value=TaskTemplateDetailState.task_template.description,
            disabled=~TaskTemplateDetailState.description_edit_mode,
            output_event=TaskTemplateDetailState.handle_description_change,
            custom_style=rx.cond(
                TaskTemplateDetailState.description_edit_mode,
                {"minHeight": "750px"},
                {"padding": "0"},
            ),
        ),
        width="100%",
        background="white",
        border_radius="8px",
        padding="1rem",
    )


def task_template_subtasks() -> rx.Component:
    """Create the subtask templates section.

    Only displayed if the task template allows subtasks.

    :return: The task template subtasks component
    :rtype: rx.Component
    """
    return rx.cond(
        TaskTemplateDetailState.task_template.allow_subtasks,
        task_template_list_component(),
        rx.center(
            rx.vstack(
                rx.icon("list_todo", size=48, color="gray"),
                rx.text("This task template does not allow subtasks", size="4", color="gray", margin_top="1rem"),
                spacing="2",
                align="center",
            ),
            padding="3rem",
            width="100%",
        ),
    )


def main_content_area() -> rx.Component:
    """Create the main content area with tabs for switching between views.

    The tab bar includes the view triggers on the left and a contextual
    action button on the right.

    :return: The main content area component
    :rtype: rx.Component
    """
    return rx.tabs.root(
        # Tab bar row: triggers on the left, action button on the right
        rx.hstack(
            rx.tabs.list(
                rx.tabs.trigger(
                    rx.hstack(
                        rx.text("Subtasks"),
                        _tab_count_badge(TaskTemplateListState.task_template_count),
                        align="center",
                        spacing="2",
                    ),
                    value="subtasks",
                ),
                rx.tabs.trigger(
                    rx.text("Description"),
                    value="description",
                ),
            ),
            rx.spacer(),
            _tab_action_button(),
            width="100%",
            align="center",
        ),
        # Tab content panels
        rx.tabs.content(
            task_template_subtasks(),
            value="subtasks",
            padding_top="1rem",
        ),
        rx.tabs.content(
            task_template_description(),
            value="description",
            padding_top="1rem",
        ),
        value=TaskTemplateDetailState.view_mode,
        on_change=TaskTemplateDetailState.set_view_mode,
        width="100%",
        flex="1",
        min_height="0",
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
    """Create the details sidebar (right side) with task template metadata.

    :return: The details sidebar component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Heading with close button
        rx.hstack(
            _sidebar_section_label("Task template details"),
            rx.spacer(),
            right_sidebar_close_button(),
            width="100%",
            align="center",
        ),
        # Parent task template (conditional)
        rx.cond(
            TaskTemplateDetailState.parent_task_template,
            rx.vstack(
                _sidebar_section_label("Parent task template"),
                rx.link(
                    TaskTemplateDetailState.parent_task_template.title,
                    href=f"/task_template/{TaskTemplateDetailState.parent_task_template.id}",
                    size="2",
                ),
                spacing="2",
                align_items="start",
                width="100%",
            ),
        ),
        # Assigned role
        rx.vstack(
            _sidebar_section_label("Assigned role"),
            rx.cond(
                TaskTemplateDetailState.task_template.assign_to_role,
                rx.badge(
                    TaskTemplateDetailState.task_template.assign_to_role,
                    variant="soft",
                    color_scheme="blue",
                    size="2",
                ),
                rx.text("Unassigned", size="2", color="gray", font_style="italic"),
            ),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Priority
        rx.vstack(
            _sidebar_section_label("Priority"),
            rx.box(
                task_priority_chip(
                    TaskTemplateDetailState.task_template.priority,
                    on_priority_change=TaskTemplateDetailState.update_priority,
                    allow_subtask=TaskTemplateDetailState.task_template.allow_subtasks,
                    size="2",
                )
            ),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Start date offset
        rx.vstack(
            _sidebar_section_label("Start date offset (days)"),
            rx.text(TaskTemplateDetailState.task_template.start_date_offset, size="2"),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Duration
        rx.vstack(
            _sidebar_section_label("Duration (days)"),
            rx.text(TaskTemplateDetailState.task_template.duration_days, size="2"),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Divider + metadata section
        rx.vstack(
            rx.divider(margin_bottom="0.5rem"),
            _sidebar_metadata_row(
                "Created by",
                user_inline_component(TaskTemplateDetailState.task_template.created_by, size="small"),
            ),
            _sidebar_metadata_row(
                "Created at",
                rx.text(
                    rx.moment(
                        TaskTemplateDetailState.task_template.created_at, format="MMM D, YYYY HH:mm"
                    ),
                    size="1",
                    weight="medium",
                ),
            ),
            _sidebar_metadata_row(
                "Last modified by",
                user_inline_component(
                    TaskTemplateDetailState.task_template.last_modified_by, size="small"
                ),
            ),
            _sidebar_metadata_row(
                "Last modified at",
                rx.text(
                    rx.moment(
                        TaskTemplateDetailState.task_template.last_modified_at,
                        format="MMM D, YYYY HH:mm",
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


def task_template_detail_page() -> rx.Component:
    """Create the task template detail page component.

    This component displays all details of a single task template using a layout
    with tabs for subtasks and description, and a details sidebar on the right.

    :return: The task template detail page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.cond(
                TaskTemplateDetailState.task_template,
                detail_page_layout(
                    main_content=main_content_area(),
                    header_content=task_template_header(),
                    header_right_content=right_sidebar_open_button(),
                ),
            ),
            header_content=breadcrumb_component(TemplateBreadcrumbState.breadcrumbs),
            right_sidebar_content=details_sidebar(),
        ),
        # Add the task template form dialog
        task_template_form_dialog(),
    )
