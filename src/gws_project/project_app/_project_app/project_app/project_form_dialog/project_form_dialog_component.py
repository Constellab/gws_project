import reflex as rx
from gws_reflex_main import form_dialog_component

from .project_form_dialog_state import ProjectFormDialogState


def _form_content() -> rx.Component:
    """Form content for entering project details."""
    return rx.vstack(
        # Form fields
        rx.vstack(
            rx.text("Project Name", size="2", weight="bold"),
            rx.input(
                placeholder="Enter project name",
                name="name",
                required=True,
                width="100%",
                default_value=ProjectFormDialogState.form_name
            ),
            width="100%",
            spacing="1"
        ),

        rx.hstack(
            rx.vstack(
                rx.text("Start Date", size="2", weight="bold"),
                rx.input(
                    type="date",
                    name="start_date",
                    required=True,
                    width="100%",
                    default_value=ProjectFormDialogState.form_start_date
                ),
                width="100%",
                spacing="1"
            ),

            rx.vstack(
                rx.text("End Date", size="2", weight="bold"),
                rx.input(
                    type="date",
                    name="end_date",
                    required=True,
                    width="100%",
                    default_value=ProjectFormDialogState.form_end_date
                ),
                width="100%",
                spacing="1"
            ),
            width="100%",
            spacing="3"
        ),

        width="100%",
        spacing="3"
    )


def _dialog() -> rx.Component:
    """The base dialog component without a trigger.

    This can be reused in different contexts with different triggers.

    :return: The dialog component
    :rtype: rx.Component
    """
    return form_dialog_component(
        state=ProjectFormDialogState,
        title=rx.cond(
            ProjectFormDialogState.is_update_mode,
            "Update Project",
            "Create New Project"
        ),
        description=rx.cond(
            ProjectFormDialogState.is_update_mode,
            "Update the project details below.",
            "Fill in the details below to create a new project."
        ),
        form_content=_form_content(),
        max_width="500px"
    )


def create_project_dialog() -> rx.Component:
    """Dialog component for creating a new project with a trigger button.

    Displays a form for entering project details. Success and error messages
    are displayed as toast notifications.

    :return: The create project dialog component with trigger button
    :rtype: rx.Component
    """
    return rx.fragment(
        rx.button(
            rx.icon("plus", size=18),
            "Create New Project",
            size="3",
            on_click=ProjectFormDialogState.open_dialog
        ),
        _dialog()
    )


def project_update_dialog() -> rx.Component:
    """Dialog component for updating an existing project.

    This component provides just the dialog (without a trigger button).
    The dialog is controlled by the ProjectFormDialogState.dialog_opened state.

    :return: The update project dialog component
    :rtype: rx.Component
    """
    return _dialog()
