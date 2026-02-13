import reflex as rx
from gws_project.template.task_template_dto import TaskTemplateDTO
from gws_reflex_main import user_inline_component

from ..common.priority_chip_component import priority_chip
from ..common.project_app_router import ProjectAppRouter


def task_template_table_component(
    task_templates: list[TaskTemplateDTO], empty_message: str = "No task templates found"
) -> rx.Component:
    """Create a reusable task template table component.

    This component displays a table of task templates with columns for title,
    dates (offset and duration), priority, assigned role, and actions menu.

    :param task_templates: List of task template DTOs to display
    :type task_templates: List[TaskTemplateDTO]
    :param empty_message: Message to display when no task templates are found
    :type empty_message: str
    :return: The task template table component
    :rtype: rx.Component
    """
    return rx.cond(
        task_templates.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Title"),
                    rx.table.column_header_cell("Start Offset (days)"),
                    rx.table.column_header_cell("Duration (days)"),
                    rx.table.column_header_cell("Priority"),
                    rx.table.column_header_cell("Assigned Role"),
                    rx.table.column_header_cell("Created By"),
                    rx.table.column_header_cell("Actions", width="100px"),
                ),
            ),
            rx.table.body(rx.foreach(task_templates, _task_template_row)),
            width="100%",
            variant="surface",
        ),
        # Empty state when no task templates
        rx.center(
            rx.vstack(
                rx.icon("list_todo", size=48, color="gray"),
                rx.text(empty_message, size="4", color="gray", margin_top="1rem"),
                spacing="2",
                align="center",
            ),
            padding="3rem",
            width="100%",
        ),
    )


def _task_template_row(task_template: TaskTemplateDTO) -> rx.Component:
    """Create a table row for a single task template.

    :param task_template: The task template data transfer object
    :type task_template: TaskTemplateDTO
    :return: The task template row component
    :rtype: rx.Component
    """
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                # Icon indicating if task template allows subtasks
                rx.cond(
                    task_template.allow_subtasks,
                    rx.icon("folder", size=16),
                    rx.icon("file", size=16),
                ),
                rx.text(
                    task_template.title,
                ),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(rx.text(task_template.start_date_offset, size="2")),
        rx.table.cell(rx.text(task_template.duration_days, size="2")),
        rx.table.cell(priority_chip(task_template.priority)),
        rx.table.cell(
            rx.cond(
                task_template.assign_to_role,
                rx.badge(task_template.assign_to_role, variant="soft", color_scheme="blue"),
                rx.text("Unassigned", size="2", color="gray"),
            )
        ),
        rx.table.cell(user_inline_component(task_template.created_by)),
        rx.table.cell(_actions_menu(task_template)),
        style={":hover": {"background_color": "var(--gray-3)"}, "cursor": "pointer"},
        on_click=lambda: rx.redirect(
            ProjectAppRouter.get_task_template_detail_url(task_template.id)
        ),
    )


def _actions_menu(task_template: TaskTemplateDTO) -> rx.Component:
    """Create the actions menu for a task template.

    :param task_template: The task template data transfer object
    :type task_template: TaskTemplateDTO
    :return: The actions menu component
    :rtype: rx.Component
    """
    from .task_template_list.task_template_list_state import TaskTemplateListState

    return rx.menu.root(
        rx.menu.trigger(rx.button(rx.icon("ellipsis-vertical", size=18), variant="soft", size="2")),
        rx.menu.content(
            rx.menu.item(
                rx.icon("pencil", size=16),
                "Update",
                on_click=lambda: TaskTemplateListState.open_update_task_template_dialog(
                    task_template.id
                ),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash-2", size=16),
                "Delete",
                color="red",
                on_click=lambda: TaskTemplateListState.open_delete_task_template_dialog(
                    task_template
                ),
            ),
            on_click=lambda: rx.stop_propagation,  # Prevent row click event
        ),
    )
