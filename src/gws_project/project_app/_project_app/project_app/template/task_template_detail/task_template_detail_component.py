import reflex as rx
from gws_reflex_main import main_component, user_inline_component
from gws_reflex_main.gws_components import rich_text_component

from ...common.detail_page_layout import detail_page_layout
from ...common.page_layout import page_layout
from ...common.priority_chip_component import priority_chip
from ...common.tasks.task_components import task_template_icon_component
from ..task_template_form_dialog.task_template_form_dialog_component import (
    task_template_form_dialog,
)
from ..task_template_list.task_template_list_component import task_template_list_component
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
                    rx.icon("ellipsis-vertical", size=18), variant="soft", color_scheme="gray"
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


def task_template_description() -> rx.Component:
    """Create the task template description section with edit/view toggle.

    :return: The task template description component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Description header with edit toggle
        rx.hstack(
            rx.heading("Description", size="4", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon(
                    rx.cond(TaskTemplateDetailState.description_edit_mode, "eye", "pencil"), size=16
                ),
                rx.cond(TaskTemplateDetailState.description_edit_mode, "View", "Edit"),
                variant="soft",
                size="2",
                on_click=TaskTemplateDetailState.toggle_description_edit_mode,
            ),
            width="100%",
            align="center",
        ),
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
        spacing="2",
        align_items="start",
    )


def task_template_subtasks() -> rx.Component:
    """Create the subtask templates section with header and list.

    Only displayed if the task template allows subtasks.

    :return: The task template subtasks component
    :rtype: rx.Component
    """
    return rx.cond(
        TaskTemplateDetailState.task_template.allow_subtasks,
        rx.vstack(
            # Header with title and create button
            rx.hstack(
                rx.heading("Subtask Templates", size="5", margin_top="1.5rem"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    "Create Subtask Template",
                    variant="soft",
                    size="2",
                    on_click=TaskTemplateDetailState.open_create_subtask_template_dialog,
                ),
                width="100%",
                align="center",
            ),
            # Subtask template list component
            task_template_list_component(),
            width="100%",
            spacing="3",
            align_items="start",
        ),
    )


def main_content_area() -> rx.Component:
    """Create the main content area (middle) with title, description, and subtask templates.

    :return: The main content area component
    :rtype: rx.Component
    """
    return rx.vstack(
        task_template_description(),
        task_template_subtasks(),
        width="100%",
        spacing="3",
        align_items="start",
        flex="1",
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
            # Parent task template (conditional row)
            rx.cond(
                TaskTemplateDetailState.parent_task_template,
                rx.fragment(
                    rx.text("Parent task template", size="2", color="gray", weight="medium"),
                    rx.link(
                        TaskTemplateDetailState.parent_task_template.title,
                        href=f"/task_template/{TaskTemplateDetailState.parent_task_template.id}",
                        size="2",
                    ),
                ),
            ),
            # Assigned role
            rx.text("Assigned role", size="2", color="gray", weight="medium"),
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
            # Priority
            rx.text("Priority", size="2", color="gray", weight="medium"),
            rx.box(
                priority_chip(
                    TaskTemplateDetailState.task_template.priority,
                    on_priority_change=TaskTemplateDetailState.update_priority,
                    allow_subtask=TaskTemplateDetailState.task_template.allow_subtasks,
                    size="2",
                )
            ),
            # Start date offset
            rx.text("Start date offset (days)", size="2", color="gray", weight="medium"),
            rx.text(TaskTemplateDetailState.task_template.start_date_offset, size="2"),
            # Duration
            rx.text("Duration (days)", size="2", color="gray", weight="medium"),
            rx.text(TaskTemplateDetailState.task_template.duration_days, size="2"),
            # Divider before technical info (spans 2 columns)
            rx.divider(margin_top="0.5rem", margin_bottom="0.5rem", grid_column="span 2"),
            # Created by
            rx.text("Created by", size="2", color="gray", weight="medium"),
            user_inline_component(TaskTemplateDetailState.task_template.created_by),
            # Created at
            rx.text("Created at", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(
                    TaskTemplateDetailState.task_template.created_at, format="MMM D, YYYY HH:mm"
                ),
                size="2",
            ),
            # Last modified by
            rx.text("Last modified by", size="2", color="gray", weight="medium"),
            user_inline_component(TaskTemplateDetailState.task_template.last_modified_by),
            # Last modified at
            rx.text("Last modified at", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(
                    TaskTemplateDetailState.task_template.last_modified_at,
                    format="MMM D, YYYY HH:mm",
                ),
                size="2",
            ),
            columns="2",
            spacing="3",
            width="100%",
            row_gap="1rem",
        ),
        width="100%",
        spacing="3",
        align_items="start",
    )


def task_template_detail() -> rx.Component:
    """Create the task template detail page component.

    This component displays all details of a single task template using a Jira-like layout
    with main content in the middle and a details sidebar on the right.

    :return: The task template detail page component
    :rtype: rx.Component
    """
    return rx.cond(
        TaskTemplateDetailState.task_template,
        detail_page_layout(
            main_content=main_content_area(),
            sidebar_content=details_sidebar(),
            breadcrumbs=TemplateBreadcrumbState.breadcrumbs,
        ),
    )


def task_template_detail_page() -> rx.Component:
    """Create the task template detail page component.

    This component displays all details of a single task template using a Jira-like layout
    with main content in the middle and a details sidebar on the right.

    :return: The task template detail page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.vstack(
                # Task template details in two-column layout
                task_template_detail(),
                width="100%",
            ),
            header_content=task_template_header(),
        ),
        # Add the task template form dialog
        task_template_form_dialog(),
    )
