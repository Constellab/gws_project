import reflex as rx

from .project_form_dialog_state import ProjectFormDialogState


def _form_content() -> rx.Component:
    """Form content for entering project details."""
    return rx.form(
        rx.vstack(
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

            rx.vstack(
                rx.text("Description", size="2", weight="bold"),
                rx.text_area(
                    placeholder="Enter project description",
                    name="description",
                    required=True,
                    width="100%",
                    rows="4",
                    default_value=ProjectFormDialogState.form_description
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

            # Action buttons
            rx.flex(
                rx.button(
                    "Cancel",
                    type="button",
                    variant="soft",
                    color_scheme="gray",
                    on_click=ProjectFormDialogState.close_dialog
                ),
                rx.button(
                    rx.cond(
                        ProjectFormDialogState._editing_project,
                        "Update Project",
                        "Create Project"
                    ),
                    type="submit"
                ),
                spacing="3",
                margin_top="1.5rem",
                justify="end"
            ),

            width="100%",
            spacing="3"
        ),
        on_submit=ProjectFormDialogState.submit_form,
        width="100%"
    )


def _dialog_content() -> rx.Component:
    """The dialog content component (without trigger).

    This can be reused in different contexts with different triggers.

    :return: The dialog content component
    :rtype: rx.Component
    """
    return rx.dialog.content(
        rx.vstack(
            rx.dialog.title(
                rx.cond(
                    ProjectFormDialogState._editing_project,
                    "Update Project",
                    "Create New Project"
                )
            ),
            rx.dialog.description(
                rx.cond(
                    ProjectFormDialogState._editing_project,
                    "Update the project details below.",
                    "Fill in the details below to create a new project."
                ),
                size="2",
                margin_bottom="1rem"
            ),

            # Form content
            _form_content(),

            width="100%"
        ),
        max_width="500px"
    )


def create_project_dialog() -> rx.Component:
    """Dialog component for creating a new project.

    Displays a form for entering project details. Success and error messages
    are displayed as toast notifications.

    :return: The create project dialog component
    :rtype: rx.Component
    """
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon("plus", size=18),
                "Create New Project",
                size="3",
                on_click=ProjectFormDialogState.open_dialog
            )
        ),
        _dialog_content(),
        open=ProjectFormDialogState.dialog_opened,
    )


def project_update_dialog() -> rx.Component:
    """Dialog component for updating an existing project.

    This component provides just the dialog (without a trigger button).
    The dialog is controlled by the ProjectFormDialogState.dialog_opened state.

    :return: The update project dialog component
    :rtype: rx.Component
    """
    return rx.dialog.root(
        _dialog_content(),
        open=ProjectFormDialogState.dialog_opened,
    )
