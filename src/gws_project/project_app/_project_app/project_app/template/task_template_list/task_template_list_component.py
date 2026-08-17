import reflex as rx
from gws_reflex_main import translate

from ..task_template_form_dialog import task_template_form_dialog
from ..task_template_table_component import task_template_table_component
from . import task_template_list_translations  # noqa: F401  (side effect: registers translations)
from .task_template_list_state import TaskTemplateListState


def task_template_list_component() -> rx.Component:
    """Create the task template list component displaying all task templates for a project template.

    This component displays a table of task templates with columns for title, dates,
    priority, assigned role, and actions menu.

    The component uses a key based on current_url_id to force remount when URL changes,
    ensuring task templates are reloaded when navigating between task templates.

    :return: The task template list component
    :rtype: rx.Component
    """
    return rx.box(
        rx.vstack(
            task_template_table_component(
                task_templates=TaskTemplateListState.get_task_templates,
            ),
            width="100%",
            spacing="3",
            align_items="start",
            # full height but not overflow parent
            flex="1",
            min_height="0",
            overflow_y="auto",
        ),
        # Key forces remount when URL changes
        key=TaskTemplateListState.current_url_id,
        width="100%",
        flex="1",
        min_height="0",
    )


def task_template_list_view() -> rx.Component:
    """Create the task templates list view with header and content.

    :return: The task templates list view component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Task templates header with create button
        rx.hstack(
            rx.heading(translate("task_template_list.heading"), size="4", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                translate("task_template_list.create_button"),
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
