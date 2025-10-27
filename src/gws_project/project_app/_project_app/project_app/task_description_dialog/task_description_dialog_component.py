import reflex as rx
from gws_reflex_main import form_dialog_component
from gws_reflex_main.gws_components import rich_text_component

from .task_description_dialog_state import TaskDescriptionDialogState


def _form_content() -> rx.Component:
    """Form content for editing task description."""
    return rx.vstack(
        # Description field
        rx.vstack(
            rx.text("Description", size="2", weight="bold"),
            rich_text_component(
                placeholder="Enter task description",
                initial_value=TaskDescriptionDialogState.form_description_rich_text,
                output_event=TaskDescriptionDialogState.handle_description_change,
                min_height="300px",
                max_height="500px",
            ),
            width="100%",
            spacing="1"
        ),
        width="100%",
        spacing="3"
    )


def task_description_dialog() -> rx.Component:
    """Dialog component for updating task description.

    This component provides a dialog with a rich text editor for updating
    the task description.

    :return: The description dialog component
    :rtype: rx.Component
    """
    return form_dialog_component(
        state=TaskDescriptionDialogState,
        title="Update Task Description",
        description="Edit the task description using the rich text editor below.",
        form_content=_form_content(),
        max_width="700px"
    )
