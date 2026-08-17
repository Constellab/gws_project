import reflex as rx
from gws_reflex_main import form_dialog_component, user_select

from ..company.company_form_dialog_component import (
    quick_create_company_dialog,
    quick_create_company_trigger_button,
)
from .project_form_dialog_state import ProjectFormDialogState


def _role_assignment_row(role: str) -> rx.Component:
    """Create a row for assigning a user to a role.

    Args:
        role: The role name

    Returns:
        Component with role name and user select dropdown
    """
    return rx.hstack(
        rx.text(
            role,
            size="2",
            weight="medium",
            min_width="120px",
        ),
        user_select(
            users=ProjectFormDialogState.available_users,
            placeholder="Select user (required)",
            on_change=lambda user_id, r=role: ProjectFormDialogState.handle_role_user_change(
                r, user_id
            ),
        ),
        width="100%",
        spacing="3",
        align="center",
    )


def _form_content() -> rx.Component:
    """Form content for entering project details."""
    return rx.vstack(
        # Project Name field
        rx.vstack(
            rx.text("Project Name*", size="2", weight="bold"),
            rx.input(
                placeholder="Enter project name",
                name="name",
                required=True,
                width="100%",
                default_value=ProjectFormDialogState.form_name,
            ),
            width="100%",
            spacing="1",
        ),
        # Company selection (optional). Only the trigger button is embedded here -
        # the actual create-company dialog/form is rendered as a page-level sibling
        # (see create_project_dialog/project_update_dialog below), never nested
        # inside this <form>: React bubbles a form's submit event through the
        # component tree even across a Dialog's portal, so a nested <form> here
        # would also (incorrectly) submit this project form.
        rx.vstack(
            rx.text("Company (optional)", size="2", weight="bold"),
            rx.hstack(
                rx.box(
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="No company",
                            width="100%",
                        ),
                        rx.select.content(
                            rx.foreach(
                                ProjectFormDialogState.available_companies,
                                lambda company: rx.select.item(
                                    company.name,
                                    value=company.id,
                                ),
                            )
                        ),
                        value=ProjectFormDialogState.form_company_id,
                        on_change=ProjectFormDialogState.set_form_company_id,
                        width="100%",
                    ),
                    flex="1",
                    min_width="0",
                ),
                quick_create_company_trigger_button(),
                width="100%",
                spacing="2",
                align="center",
            ),
            width="100%",
            spacing="1",
        ),
        # Manager selection (only in update mode)
        rx.cond(
            ProjectFormDialogState.is_update_mode,
            rx.vstack(
                rx.text("Manager", size="2", weight="bold"),
                user_select(
                    users=ProjectFormDialogState.project_users,
                    placeholder="Select project manager",
                    default_value=ProjectFormDialogState.form_project_manager_id,
                    name="project_manager_id",
                    width="100%",
                ),
                width="100%",
                spacing="1",
            ),
        ),
        # Template selection (only in create mode)
        rx.cond(
            ~ProjectFormDialogState.is_update_mode,
            rx.vstack(
                rx.text("Project Template (Optional)", size="2", weight="bold"),
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Select a template (optional)",
                        width="100%",
                    ),
                    rx.select.content(
                        rx.foreach(
                            ProjectFormDialogState.available_templates,
                            lambda template: rx.select.item(
                                template.name,
                                value=template.id,
                            ),
                        )
                    ),
                    value=ProjectFormDialogState.selected_template_id,
                    on_change=ProjectFormDialogState.handle_template_change,
                ),
                width="100%",
                spacing="1",
            ),
        ),
        # Date fields
        rx.hstack(
            rx.vstack(
                rx.text("Start Date*", size="2", weight="bold"),
                rx.input(
                    type="date",
                    name="start_date",
                    required=True,
                    width="100%",
                    default_value=ProjectFormDialogState.form_start_date,
                ),
                width="100%",
                spacing="1",
            ),
            # End Date (hidden when template is selected)
            rx.cond(
                ProjectFormDialogState.selected_template_id == "",
                rx.vstack(
                    rx.text("End Date*", size="2", weight="bold"),
                    rx.input(
                        type="date",
                        name="end_date",
                        required=True,
                        width="100%",
                        default_value=ProjectFormDialogState.form_end_date,
                    ),
                    width="100%",
                    spacing="1",
                ),
            ),
            width="100%",
            spacing="3",
        ),
        # Role assignments (only when template is selected and has roles)
        rx.cond(
            (ProjectFormDialogState.selected_template_id != "")
            & (ProjectFormDialogState.template_roles.length() > 0),
            rx.vstack(
                rx.text("Role Assignments", size="2", weight="bold"),
                rx.text(
                    "Assign a user to each role. These users will be added to the project and assigned to the corresponding tasks.",
                    size="1",
                    color="gray",
                ),
                rx.box(
                    rx.vstack(
                        rx.foreach(ProjectFormDialogState.template_roles, _role_assignment_row),
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


def _dialog() -> rx.Component:
    """The base dialog component without a trigger.

    This can be reused in different contexts with different triggers.

    :return: The dialog component
    :rtype: rx.Component
    """
    return form_dialog_component(
        state=ProjectFormDialogState,
        title=rx.cond(ProjectFormDialogState.is_update_mode, "Update Project", "New Project"),
        description=rx.cond(
            ProjectFormDialogState.is_update_mode,
            "Update the project details below.",
            "Fill in the details below to create a new project.",
        ),
        form_content=_form_content(),
        max_width="500px",
        # Opening the quick-create company dialog on top of this one moves focus
        # to that nested dialog, which Radix's dismissable layer treats as an
        # "outside interaction" on this dialog and would otherwise close it.
        # Disabling outside-click/escape dismissal here means this dialog can
        # only be closed via Cancel/Save/the close icon, which also avoids
        # accidentally losing a partially-filled project form.
        dismissable=False,
    )


def create_project_dialog() -> rx.Component:
    """Dialog component for creating a new project with a trigger button.

    Displays a form for entering project details. Success and error messages
    are displayed as toast notifications.

    Also renders the quick-create company dialog as a sibling (not nested inside
    the project's own <form> - see the comment in _form_content for why).

    :return: The create project dialog component with trigger button
    :rtype: rx.Component
    """
    return rx.fragment(
        rx.button(
            rx.icon("plus", size=18),
            "New Project",
            size="3",
            on_click=ProjectFormDialogState.open_create_dialog,
        ),
        _dialog(),
        quick_create_company_dialog(),
    )


def project_update_dialog() -> rx.Component:
    """Dialog component for updating an existing project.

    This component provides just the dialog (without a trigger button).
    The dialog is controlled by the ProjectFormDialogState.dialog_opened state.

    Also renders the quick-create company dialog as a sibling (not nested inside
    the project's own <form> - see the comment in _form_content for why).

    :return: The update project dialog component
    :rtype: rx.Component
    """
    return rx.fragment(
        _dialog(),
        quick_create_company_dialog(),
    )
