import reflex as rx
from gws_reflex_main import (
    main_component,
    right_sidebar_close_button,
    user_inline_component,
)
from gws_reflex_main.gws_components import rich_text_component

from ..common.breadcrumb.breadcrumb_component import breadcrumb_component
from ..common.detail_page_layout import detail_page_layout
from ..common.page_layout import page_layout
from .note_detail_state import NoteDetailState


def _note_actions_menu() -> rx.Component:
    """Create the actions menu (Rename, Delete) for the note.

    :return: The actions menu component
    :rtype: rx.Component
    """
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("ellipsis-vertical", size=18),
                variant="ghost",
                size="2",
            ),
            margin_left="0",
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("pencil", size=16),
                "Rename",
                on_click=NoteDetailState.open_rename_dialog,
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash-2", size=16),
                "Delete",
                color_scheme="red",
                on_click=NoteDetailState.open_delete_dialog,
            ),
        ),
    )


def note_header() -> rx.Component:
    """Create the note header with icon, title and actions menu.

    :return: The note header component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.icon("notebook-pen", size=24),
        rx.heading(
            NoteDetailState.note.name,
            size="6",
        ),
        rx.spacer(),
        _note_actions_menu(),
        width="100%",
        align="center",
        spacing="2",
    )


def _rename_note_dialog() -> rx.Component:
    """Create the rename note dialog.

    :return: The rename dialog component
    :rtype: rx.Component
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Rename Note"),
            rx.form(
                rx.flex(
                    rx.text(
                        "Note Name",
                        as_="div",
                        size="2",
                        margin_bottom="4px",
                        weight="bold",
                    ),
                    rx.input(
                        value=NoteDetailState.rename_note_name,
                        on_change=NoteDetailState.set_rename_note_name,
                        placeholder="Enter note name",
                        name="name",
                        required=True,
                    ),
                    direction="column",
                    spacing="3",
                ),
                rx.flex(
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            type="button",
                            on_click=NoteDetailState.close_rename_dialog,
                            disabled=NoteDetailState.is_renaming,
                        ),
                    ),
                    rx.button(
                        rx.cond(
                            NoteDetailState.is_renaming,
                            rx.hstack(
                                rx.spinner(size="2"),
                                "Renaming...",
                                spacing="2",
                            ),
                            "Rename",
                        ),
                        type="submit",
                        disabled=NoteDetailState.is_renaming,
                    ),
                    padding_top="16px",
                    spacing="3",
                    margin_top="16px",
                    justify="end",
                ),
                on_submit=lambda _: NoteDetailState.handle_rename_note(),
                reset_on_submit=False,
            ),
            style={"max_width": 450},
            on_interact_outside=NoteDetailState.close_rename_dialog,
            on_escape_key_down=NoteDetailState.close_rename_dialog,
        ),
        open=NoteDetailState.rename_dialog_open,
    )


def _note_content() -> rx.Component:
    """Create the rich-text editor area for the note.

    The content is saved automatically on change.

    :return: The note content component
    :rtype: rx.Component
    """
    return rx.vstack(
        rich_text_component(
            value=NoteDetailState.note_content,
            disabled=False,
            output_event=NoteDetailState.handle_content_change,
            custom_style={"flex": "1", "display": "flex", "backgroundColor": "white"},
        ),
        width="100%",
        spacing="3",
        align_items="start",
        flex="1",
        min_height="0",
    )


def _sidebar_section_label(label: str) -> rx.Component:
    """Create a small uppercase gray label for a sidebar section.

    :param label: The label text
    :type label: str
    :return: The styled label component
    :rtype: rx.Component
    """
    return rx.text(
        label,
        size="1",
        color="gray",
        weight="bold",
        style={
            "text-transform": "uppercase",
            "letter-spacing": "0.06em",
        },
    )


def _sidebar_metadata_row(label: str, value: rx.Component) -> rx.Component:
    """Create a metadata row with a label on the left and value on the right.

    :param label: The label text
    :type label: str
    :param value: The value component
    :type value: rx.Component
    :return: The metadata row component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.text(label, size="2", color="gray"),
        rx.spacer(),
        value,
        width="100%",
        align="center",
    )


def details_sidebar() -> rx.Component:
    """Create the details sidebar (right side) with note metadata.

    :return: The details sidebar component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Heading with close button
        rx.hstack(
            _sidebar_section_label("Note details"),
            rx.spacer(),
            right_sidebar_close_button(),
            width="100%",
            align="center",
        ),
        # Metadata section
        rx.vstack(
            _sidebar_metadata_row(
                "Created by",
                user_inline_component(NoteDetailState.note.created_by, size="small"),
            ),
            _sidebar_metadata_row(
                "Created at",
                rx.text(
                    rx.moment(NoteDetailState.note.created_at, format="MMM D, YYYY HH:mm"),
                    size="1",
                    weight="medium",
                ),
            ),
            _sidebar_metadata_row(
                "Last modified by",
                user_inline_component(NoteDetailState.note.last_modified_by, size="small"),
            ),
            _sidebar_metadata_row(
                "Last modified at",
                rx.text(
                    rx.moment(NoteDetailState.note.last_modified_at, format="MMM D, YYYY HH:mm"),
                    size="1",
                    weight="medium",
                ),
            ),
            spacing="1",
            width="100%",
        ),
        width="100%",
        spacing="5",
        align_items="start",
    )


def note_detail_page() -> rx.Component:
    """Create the note detail page component.

    This page displays a single NOTE document in a full-page rich-text editor
    with a details sidebar, matching the task detail layout. It replaces the
    former note editor dialog.

    :return: The note detail page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.cond(
                NoteDetailState.note,
                detail_page_layout(
                    main_content=_note_content(),
                    header_content=note_header(),
                ),
            ),
            right_sidebar_content=details_sidebar(),
            header_content=breadcrumb_component(NoteDetailState.breadcrumbs),
            max_content_width="1200px",
            height="100vh",
            padding="0",
        ),
        # Rename note dialog (delete uses the global ConfirmDialogState)
        _rename_note_dialog(),
    )
