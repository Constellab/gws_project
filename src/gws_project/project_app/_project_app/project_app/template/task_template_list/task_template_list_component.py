import reflex as rx

from ..task_template_form_dialog import task_template_form_dialog
from ..task_template_table_component import task_template_table_component
from .task_template_list_state import TaskTemplateListState


def task_template_list_component() -> rx.Component:
    """Create the task template list component displaying all task templates for a project template.

    This component displays a table of task templates with columns for title, dates,
    priority, assigned role, and actions menu.

    :return: The task template list component
    :rtype: rx.Component
    """
    return rx.vstack(
        task_template_table_component(
            task_templates=TaskTemplateListState.get_task_templates,
            empty_message="No task templates found"
        ),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
        overflow_y="auto",
    )


def task_template_list_view() -> rx.Component:
    """Create the task templates list view with header and content.

    :return: The task templates list view component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Task templates header with create button
        rx.hstack(
            rx.heading("Task Templates", size="4", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "Create Task Template",
                variant="soft",
                size="2",
                on_click=TaskTemplateListState.open_create_task_template_dialog
            ),
            width="100%",
            align="center"
        ),
        # Task templates list content
        task_template_list_component(),
        # Task template form dialog
        task_template_form_dialog(),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
    )
