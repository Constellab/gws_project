import reflex as rx
from gws_reflex_main import form_dialog_component

from .project_template_form_dialog_state import ProjectTemplateFormDialogState


def _form_content() -> rx.Component:
    """Form content for entering template details."""
    return rx.vstack(
        # Form fields
        rx.vstack(
            rx.text("Template Name*", size="2", weight="bold"),
            rx.input(
                placeholder="Enter template name",
                name="name",
                required=True,
                width="100%",
                default_value=ProjectTemplateFormDialogState.form_name,
            ),
            width="100%",
            spacing="1",
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
        state=ProjectTemplateFormDialogState,
        title=rx.cond(
            ProjectTemplateFormDialogState.is_update_mode, "Update Template", "Create New Template"
        ),
        description=rx.cond(
            ProjectTemplateFormDialogState.is_update_mode,
            "Update the template details below.",
            "Fill in the details below to create a new template.",
        ),
        form_content=_form_content(),
        max_width="500px",
    )


def create_template_dialog() -> rx.Component:
    """Dialog component for creating a new template with a trigger button.

    Displays a form for entering template details. Success and error messages
    are displayed as toast notifications.

    :return: The create template dialog component with trigger button
    :rtype: rx.Component
    """
    return rx.fragment(
        rx.button(
            rx.icon("plus", size=18),
            "Create New Template",
            size="3",
            on_click=ProjectTemplateFormDialogState.open_dialog,
        ),
        _dialog(),
    )


def project_template_update_dialog() -> rx.Component:
    """Dialog component for updating an existing template.

    This component provides just the dialog (without a trigger button).
    The dialog is controlled by the TemplateFormDialogState.dialog_opened state.

    :return: The update template dialog component
    :rtype: rx.Component
    """
    return _dialog()
