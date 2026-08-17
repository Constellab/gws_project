import reflex as rx
from gws_reflex_main import translate

from ..common.project_app_router import ProjectAppRouter
from ..common.tasks.task_components import task_template_icon_component
from ..common.tasks.task_priority_chip_component import task_priority_chip
from .task_template_list import (
    task_template_list_translations,  # noqa: F401  (side effect: registers translations)
)
from .task_template_list.task_template_list_state import TaskTemplateListState, TaskTemplateRowDTO


def task_template_table_component(
    task_templates: list[TaskTemplateRowDTO],
    empty_message: str | rx.Var[str] | None = None,
) -> rx.Component:
    """Create a reusable task template table component.

    This component displays a table of task templates with columns for title,
    dates (offset and duration), priority, assigned role, and actions menu.

    Templates are expected to already be sorted by start offset (ascending); the
    actions menu lets the user reorder templates that share the same offset.

    :param task_templates: List of task template rows to display
    :type task_templates: List[TaskTemplateRowDTO]
    :param empty_message: Message to display when no task templates are found
    :type empty_message: str
    :return: The task template table component
    :rtype: rx.Component
    """
    resolved_empty_message = (
        translate("task_template_table.empty_message") if empty_message is None else empty_message
    )
    return rx.cond(
        task_templates.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(translate("task_template_table.column_title")),
                    rx.table.column_header_cell(
                        translate("task_template_table.column_start_offset")
                    ),
                    rx.table.column_header_cell(translate("task_template_table.column_duration")),
                    rx.table.column_header_cell(translate("task_template_table.column_priority")),
                    rx.table.column_header_cell(
                        translate("task_template_table.column_assigned_role")
                    ),
                    rx.table.column_header_cell(
                        translate("task_template_table.column_actions"), width="100px"
                    ),
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
                rx.text(resolved_empty_message, size="4", color="gray", margin_top="1rem"),
                spacing="2",
                align="center",
            ),
            padding="3rem",
            width="100%",
        ),
    )


def _task_template_row(row: TaskTemplateRowDTO) -> rx.Component:
    """Create a table row for a single task template.

    :param row: The task template row (template + move up/down eligibility)
    :type row: TaskTemplateRowDTO
    :return: The task template row component
    :rtype: rx.Component
    """
    task_template = row.template
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                # Icon indicating if task template allows subtasks
                task_template_icon_component(task_template, size="3"),
                rx.text(
                    task_template.title,
                ),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(
            rx.text(rx.cond(task_template.start_date_offset.is_not_none(), task_template.start_date_offset, "—"), size="2")
        ),
        rx.table.cell(
            rx.text(rx.cond(task_template.duration_days.is_not_none(), task_template.duration_days, "—"), size="2")
        ),
        rx.table.cell(task_priority_chip(task_template.priority)),
        rx.table.cell(
            rx.cond(
                task_template.assign_to_role,
                rx.badge(task_template.assign_to_role, variant="soft", color_scheme="blue"),
                rx.text(translate("task_template_table.unassigned"), size="2", color="gray"),
            )
        ),
        rx.table.cell(_actions_menu(row)),
        style={":hover": {"background_color": "var(--gray-3)"}, "cursor": "pointer"},
        on_click=lambda: rx.redirect(
            ProjectAppRouter.get_task_template_detail_url(task_template.id)
        ),
    )


def _actions_menu(row: TaskTemplateRowDTO) -> rx.Component:
    """Create the actions menu for a task template.

    Includes "Move up"/"Move down" to reorder templates that share the same start
    offset (start_date_offset is always the primary order, so these items only
    appear when there's an adjacent sibling with the same offset to swap with).

    :param row: The task template row (template + move up/down eligibility)
    :type row: TaskTemplateRowDTO
    :return: The actions menu component
    :rtype: rx.Component
    """
    task_template = row.template

    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("ellipsis-vertical", size=18),
                variant="ghost",
                color_scheme="gray",
                size="2",
            )
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("pencil", size=16),
                translate("task_template_table.update"),
                on_click=lambda: TaskTemplateListState.open_update_task_template_dialog(
                    task_template.id
                ),
            ),
            rx.cond(
                row.can_move_up,
                rx.menu.item(
                    rx.icon("arrow-up", size=16),
                    translate("task_template_table.move_up"),
                    on_click=lambda: TaskTemplateListState.move_task_template_up(task_template.id),
                ),
            ),
            rx.cond(
                row.can_move_down,
                rx.menu.item(
                    rx.icon("arrow-down", size=16),
                    translate("task_template_table.move_down"),
                    on_click=lambda: TaskTemplateListState.move_task_template_down(
                        task_template.id
                    ),
                ),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash-2", size=16),
                translate("task_template_table.delete"),
                color_scheme="red",
                on_click=lambda: TaskTemplateListState.open_delete_task_template_dialog(
                    task_template
                ),
            ),
            on_click=lambda: rx.stop_propagation,  # Prevent row click event
        ),
    )
