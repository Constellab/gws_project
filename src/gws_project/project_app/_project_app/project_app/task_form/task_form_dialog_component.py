import reflex as rx
from gws_project.task.task_dto import TaskPriority, TaskStatus
from gws_reflex_main import form_dialog_component, translate, user_select

from . import task_form_dialog_translations  # noqa: F401  (side effect: registers translations)
from .task_form_dialog_state import TaskFormDialogState


def _role_assignment_row(role: str) -> rx.Component:
    """Create a row for assigning a project member to a template role.

    :param role: The role name
    :type role: str
    :return: Component with role name and user select dropdown
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.text(role, size="2", weight="medium", min_width="120px"),
        user_select(
            users=TaskFormDialogState.users,
            placeholder=translate("task_form.role_user_select_placeholder"),
            # Bound to the mapping so the select is controlled rather than keeping its own
            # state: rx.foreach reconciles rows by position and emits no React key, so an
            # uncontrolled select would keep showing the user picked for the role that used
            # to sit in this row after the template - and its role list - changed.
            value=TaskFormDialogState.role_mapping.get(role, ""),
            on_change=lambda user_id, r=role: TaskFormDialogState.handle_role_user_change(
                r, user_id
            ),
        ),
        width="100%",
        spacing="3",
        align="center",
    )


def _template_picker() -> rx.Component:
    """Task template selector (only shown when creating a root task)."""
    return rx.cond(
        TaskFormDialogState.is_create_root_mode,
        rx.vstack(
            rx.text(translate("task_form.template.label"), size="2", weight="bold"),
            rx.select.root(
                rx.select.trigger(
                    placeholder=translate("task_form.template.placeholder"),
                    width="100%",
                ),
                rx.select.content(
                    rx.foreach(
                        TaskFormDialogState.available_templates,
                        lambda template: rx.select.item(
                            template.name,
                            value=template.id,
                        ),
                    )
                ),
                value=TaskFormDialogState.selected_template_id,
                on_change=TaskFormDialogState.handle_template_change,
            ),
            width="100%",
            spacing="1",
        ),
    )


def _single_task_fields() -> rx.Component:
    """Fields for creating/updating a single task (hidden when a template is selected)."""
    return rx.fragment(
        # Title field
        rx.vstack(
            rx.text(translate("task_form.title_field.label"), size="2", weight="bold"),
            rx.input(
                placeholder=translate("task_form.title_field.placeholder"),
                name="title",
                required=True,
                width="100%",
                default_value=TaskFormDialogState.form_title
            ),
            width="100%",
            spacing="1"
        ),

        # Assign to field (shown in both create and update modes)
        rx.vstack(
            rx.text(translate("task_form.assign_to.label"), size="2", weight="bold"),
            user_select(
                users=TaskFormDialogState.users,
                placeholder=translate("task_form.assign_to.placeholder"),
                name="assign_to_id",
                default_value=TaskFormDialogState.form_assign_to_id,
                width="100%",
            ),
            width="100%",
            spacing="1"
        ),

        # Task type radio buttons (shown in both create root and create sub modes, hidden in update mode)
        rx.cond(
            ~TaskFormDialogState.is_update_mode,
            rx.vstack(
                rx.text(translate("task_form.task_type.label"), size="2", weight="bold"),
                rx.radio.root(
                    rx.hstack(
                        rx.radio.item(
                            rx.hstack(
                                rx.text(translate("task_form.task_type.single"), size="2"),
                                spacing="2",
                                align="center"
                            ),
                            value="without_children"
                        ),
                        rx.radio.item(
                            rx.hstack(
                                rx.text(translate("task_form.task_type.with_subtasks"), size="2"),
                                spacing="2",
                                align="center"
                            ),
                            value="with_children"
                        ),
                        spacing="4"
                    ),
                    default_value=TaskFormDialogState.selected_task_type,
                    value=TaskFormDialogState.selected_task_type,
                    on_change=TaskFormDialogState.set_selected_task_type,
                    name="allow_subtasks"
                ),
                width="100%",
                spacing="1"
            )
        ),

        # Date fields and Priority/Status (conditionally shown)
        rx.cond(
            TaskFormDialogState.should_show_dates_and_priority,
            rx.vstack(
                # Date fields
                rx.hstack(
                    rx.vstack(
                        rx.text(translate("task_form.start_date.label"), size="2", weight="bold"),
                        rx.input(
                            type="date",
                            name="start_date",
                            width="100%",
                            default_value=TaskFormDialogState.form_start_date,
                            min=TaskFormDialogState.get_min_start_date,
                            max=TaskFormDialogState.get_max_due_date,
                        ),
                        width="100%",
                        spacing="1"
                    ),

                    rx.vstack(
                        rx.text(translate("task_form.due_date.label"), size="2", weight="bold"),
                        rx.input(
                            type="date",
                            name="due_date",
                            width="100%",
                            default_value=TaskFormDialogState.form_due_date,
                            min=TaskFormDialogState.get_min_start_date,
                            max=TaskFormDialogState.get_max_due_date,
                        ),
                        width="100%",
                        spacing="1"
                    ),
                    width="100%",
                    spacing="3"
                ),


                # Create mode: show both status and priority
                rx.hstack(
                    rx.vstack(
                        rx.text(translate("task_form.status.label"), size="2", weight="bold"),
                        rx.select(
                            [status.value for status in TaskStatus],
                            name="status",
                            default_value=TaskFormDialogState.form_status,
                            width="100%",
                        ),
                        width="100%",
                        spacing="1"
                    ),

                    rx.vstack(
                        rx.text(translate("task_form.priority.label"), size="2", weight="bold"),
                        rx.select(
                            [priority.value for priority in TaskPriority],
                            name="priority",
                            default_value=TaskFormDialogState.form_priority,
                            width="100%",
                        ),
                        width="100%",
                        spacing="1"
                    ),
                    width="100%",
                    spacing="3"
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
                        translate("task_form.auto_calc_message"),
                        size="2"
                    ),
                ),
                width="100%",
                spacing="1"
            )
        ),
    )


def _template_fields() -> rx.Component:
    """Fields for bulk-creating tasks from a template: a reference start date and,
    if the template defines roles, a project-member picker for each one."""
    return rx.vstack(
        rx.vstack(
            rx.text(translate("task_form.template_start_date.label"), size="2", weight="bold"),
            rx.input(
                type="date",
                name="start_date",
                required=True,
                width="100%",
                default_value=TaskFormDialogState.form_start_date,
                min=TaskFormDialogState.get_min_start_date,
                max=TaskFormDialogState.get_max_due_date,
            ),
            width="100%",
            spacing="1"
        ),
        rx.cond(
            TaskFormDialogState.template_roles.length() > 0,
            rx.vstack(
                rx.text(translate("task_form.role_assignments.label"), size="2", weight="bold"),
                rx.text(
                    translate("task_form.role_assignments.description"),
                    size="1",
                    color="gray",
                ),
                rx.box(
                    rx.vstack(
                        rx.foreach(TaskFormDialogState.template_roles, _role_assignment_row),
                        width="100%",
                        spacing="2",
                    ),
                    padding="0.5rem",
                    border="1px solid var(--gray-6)",
                    border_radius="0.5rem",
                    width="100%",
                ),
                width="100%",
                spacing="1",
            ),
        ),
        width="100%",
        spacing="3",
    )


def _form_content() -> rx.Component:
    """Form content for entering task details, or picking a template to bulk-create
    tasks from instead (mirrors the "New Project" dialog's template picker)."""
    return rx.vstack(
        _template_picker(),
        rx.cond(
            TaskFormDialogState.selected_template_id == "",
            _single_task_fields(),
            _template_fields(),
        ),
        width="100%",
        spacing="3"
    )


def task_form_dialog() -> rx.Component:
    """Dialog component for creating or updating a task.

    This component provides the dialog (without a trigger button).
    The dialog is controlled by the TaskFormDialogState.dialog_opened state.

    :return: The task form dialog component
    :rtype: rx.Component
    """
    return form_dialog_component(
        state=TaskFormDialogState,
        title=rx.cond(
            TaskFormDialogState.is_update_mode, translate("task_form.title.update"), rx.cond(
                TaskFormDialogState.is_create_sub_mode,
                translate("task_form.title.create_sub"),
                translate("task_form.title.create_root"))
        ),
        form_content=_form_content(),
        max_width="600px"
    )
