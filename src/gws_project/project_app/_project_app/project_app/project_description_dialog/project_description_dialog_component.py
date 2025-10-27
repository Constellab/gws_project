import reflex as rx
from gws_reflex_main import form_dialog_component
from gws_reflex_main.gws_components import rich_text_component

from .project_description_dialog_state import ProjectDescriptionDialogState


def _form_content() -> rx.Component:
    """Form content for editing project description."""
    return rx.vstack(
        # Description field
        rx.vstack(
            rx.text("Description", size="2", weight="bold"),
            rich_text_component(
                placeholder="Enter project description",
                initial_value=ProjectDescriptionDialogState.form_description_rich_text,
                output_event=ProjectDescriptionDialogState.handle_description_change,
                min_height="500px",
            ),
            width="100%",
            spacing="1"
        ),
        width="100%",
        spacing="3"
    )


def project_description_dialog() -> rx.Component:
    """Dialog component for updating project description.

    This component provides a dialog with a rich text editor for updating
    the project description.

    :return: The description dialog component
    :rtype: rx.Component
    """
    return form_dialog_component(
        state=ProjectDescriptionDialogState,
        title="Update Project Description",
        description="Edit the project description using the rich text editor below.",
        form_content=_form_content(),
        max_width="700px"
    )
