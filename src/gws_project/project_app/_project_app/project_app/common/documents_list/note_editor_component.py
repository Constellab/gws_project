import reflex as rx
from gws_reflex_main.gws_components import rich_text_component

from .note_editor_state import NoteEditorState


def note_editor_dialog() -> rx.Component:
    """Create the note editor dialog.

    Displays the rich-text editor for the opened note. The content is saved
    automatically on change.

    :return: The note editor dialog component
    :rtype: rx.Component
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.dialog.title(NoteEditorState.note_name, margin_bottom="0"),
                rx.spacer(),
                rx.dialog.close(
                    rx.icon_button(
                        rx.icon("x", size=18),
                        variant="ghost",
                        color_scheme="gray",
                        on_click=NoteEditorState.close_dialog,
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.box(
                rich_text_component(
                    value=NoteEditorState.note_content,
                    disabled=False,
                    output_event=NoteEditorState.handle_content_change,
                    custom_style={"flex": "1", "display": "flex", "backgroundColor": "white"},
                ),
                width="100%",
                flex="1",
                min_height="0",
                overflow_y="auto",
                margin_top="1rem",
            ),
            style={"max_width": "60rem", "height": "80vh"},
            display="flex",
            flex_direction="column",
            on_interact_outside=NoteEditorState.close_dialog,
            on_escape_key_down=NoteEditorState.close_dialog,
        ),
        open=NoteEditorState.dialog_open,
    )
