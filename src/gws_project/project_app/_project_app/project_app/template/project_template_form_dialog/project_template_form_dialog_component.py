import reflex as rx
from gws_reflex_main import form_dialog_component, translate

from . import (
    project_template_form_dialog_translations,  # noqa: F401  (side effect: registers translations)
)
from .project_template_form_dialog_state import ProjectTemplateFormDialogState


def _form_content() -> rx.Component:
    """Form content for entering template details."""
    return rx.vstack(
        # Form fields
        rx.vstack(
            rx.text(translate("project_template_form_dialog.name_label"), size="2", weight="bold"),
            rx.input(
                placeholder=translate("project_template_form_dialog.name_placeholder"),
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
            ProjectTemplateFormDialogState.is_update_mode,
            translate("project_template_form_dialog.update_title"),
            translate("project_template_form_dialog.create_title"),
        ),
        description=rx.cond(
            ProjectTemplateFormDialogState.is_update_mode,
            translate("project_template_form_dialog.update_description"),
            translate("project_template_form_dialog.create_description"),
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
            translate("project_template_form_dialog.create_title"),
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
