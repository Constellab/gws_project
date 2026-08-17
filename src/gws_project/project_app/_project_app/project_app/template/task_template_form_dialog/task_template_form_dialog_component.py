import reflex as rx
from gws_project.task.task_dto import TaskPriority
from gws_reflex_main import form_dialog_component, translate

from . import (
    task_template_form_dialog_translations,  # noqa: F401  (side effect: registers translations)
)
from .task_template_form_dialog_state import TaskTemplateFormDialogState


def _form_content() -> rx.Component:
    """Form content for entering task template details."""
    return rx.vstack(
        # Title field
        rx.vstack(
            rx.text(translate("task_template_form_dialog.title_label"), size="2", weight="bold"),
            rx.input(
                placeholder=translate("task_template_form_dialog.title_placeholder"),
                name="title",
                required=True,
                width="100%",
                default_value=TaskTemplateFormDialogState.form_title
            ),
            width="100%",
            spacing="1"
        ),

        # Task type radio buttons (shown in both create root and create sub modes, hidden in update mode)
        rx.cond(
            ~TaskTemplateFormDialogState.is_update_mode,
            rx.vstack(
                rx.text(translate("task_template_form_dialog.type_label"), size="2", weight="bold"),
                rx.radio.root(
                    rx.hstack(
                        rx.radio.item(
                            rx.hstack(
                                rx.text(translate("task_template_form_dialog.type_single"), size="2"),
                                spacing="2",
                                align="center"
                            ),
                            value="without_children"
                        ),
                        rx.radio.item(
                            rx.hstack(
                                rx.text(
                                    translate("task_template_form_dialog.type_with_subtasks"), size="2"
                                ),
                                spacing="2",
                                align="center"
                            ),
                            value="with_children"
                        ),
                        spacing="4"
                    ),
                    default_value=TaskTemplateFormDialogState.selected_task_type,
                    value=TaskTemplateFormDialogState.selected_task_type,
                    on_change=TaskTemplateFormDialogState.set_selected_task_type,
                    name="allow_subtasks"
                ),
                width="100%",
                spacing="1"
            )
        ),

        # Date offset and duration fields (conditionally shown)
        rx.cond(
            TaskTemplateFormDialogState.should_show_dates_and_priority,
            rx.vstack(
                # Date offset and duration fields
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            translate("task_template_form_dialog.start_offset_label"),
                            size="2",
                            weight="bold",
                        ),
                        rx.input(
                            type="number",
                            name="start_date_offset",
                            width="100%",
                            default_value=TaskTemplateFormDialogState.form_start_date_offset,
                            min="0",
                            placeholder=translate("task_template_form_dialog.start_offset_placeholder")
                        ),
                        width="100%",
                        spacing="1"
                    ),

                    rx.vstack(
                        rx.text(
                            translate("task_template_form_dialog.duration_label"),
                            size="2",
                            weight="bold",
                        ),
                        rx.input(
                            type="number",
                            name="duration_days",
                            width="100%",
                            default_value=TaskTemplateFormDialogState.form_duration_days,
                            min="1",
                            placeholder=translate("task_template_form_dialog.duration_placeholder")
                        ),
                        width="100%",
                        spacing="1"
                    ),
                    width="100%",
                    spacing="3"
                ),

                # Priority field
                rx.vstack(
                    rx.text(translate("task_template_form_dialog.priority_label"), size="2", weight="bold"),
                    rx.select(
                        [priority.value for priority in TaskPriority],
                        name="priority",
                        default_value=TaskTemplateFormDialogState.form_priority,
                        width="100%",
                    ),
                    width="100%",
                    spacing="1"
                ),
                width="100%",
            ),

            # When dates and priority are hidden, show a message explaining auto-calculation
            rx.vstack(
                rx.callout.root(
                    rx.callout.icon(
                        rx.icon(tag="info", size=16)
                    ),
                    rx.callout.text(
                        rx.cond(
                            TaskTemplateFormDialogState.is_create_sub_mode,
                            translate("task_template_form_dialog.info_create_sub"),
                            rx.cond(
                                TaskTemplateFormDialogState.is_parent_task_in_update_mode,
                                translate("task_template_form_dialog.info_update_parent"),
                                translate("task_template_form_dialog.info_create_parent")
                            )
                        ),
                        size="2"
                    ),
                ),
                width="100%",
                spacing="1"
            )
        ),

        # Assign to role field
        rx.vstack(
            rx.text(translate("task_template_form_dialog.role_label"), size="2", weight="bold"),
            rx.text(
                translate("task_template_form_dialog.role_description"),
                size="1",
                color="gray",
            ),
            rx.input(
                placeholder=translate("task_template_form_dialog.role_placeholder"),
                name="assign_to_role",
                width="100%",
                default_value=TaskTemplateFormDialogState.form_assign_to_role
            ),
            width="100%",
            spacing="1"
        ),

        width="100%",
        spacing="3"
    )


def task_template_form_dialog() -> rx.Component:
    """Dialog component for creating or updating a task template.

    This component provides the dialog (without a trigger button).
    The dialog is controlled by the TaskTemplateFormDialogState.dialog_opened state.

    :return: The task template form dialog component
    :rtype: rx.Component
    """
    return form_dialog_component(
        state=TaskTemplateFormDialogState, title=rx.cond(
            TaskTemplateFormDialogState.is_update_mode,
            translate("task_template_form_dialog.title_update"), rx.cond(
                TaskTemplateFormDialogState.is_create_sub_mode,
                translate("task_template_form_dialog.title_create_sub"),
                translate("task_template_form_dialog.title_create_root"))),
        description=rx.cond(
            TaskTemplateFormDialogState.is_update_mode, rx.cond(
                TaskTemplateFormDialogState.is_parent_task_in_update_mode,
                translate("task_template_form_dialog.description_update_parent"),
                translate("task_template_form_dialog.description_update")),
            rx.cond(
                TaskTemplateFormDialogState.is_create_sub_mode,
                translate("task_template_form_dialog.description_create_sub"),
                translate("task_template_form_dialog.description_create_root"))),
        form_content=_form_content(),
        max_width="600px")
