import reflex as rx
from gws_reflex_main import translate

from . import documents_list_translations  # noqa: F401  (side effect: registers translations)
from .document_card_component import document_card
from .documents_list_state import DocumentsListState


def documents_list_view() -> rx.Component:
    """Create the documents view with header and content.

    :return: The documents view component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Documents header with action buttons
        rx.hstack(
            rx.heading(translate("documents_list.title"), size="4", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("file-plus", size=16),
                translate("documents_list.create_note"),
                variant="soft",
                size="2",
                on_click=DocumentsListState.open_create_note_dialog,
            ),
            rx.upload.root(
                rx.button(
                    rx.spinner(loading=DocumentsListState.is_uploading),
                    rx.icon("upload", size=16),
                    translate("documents_list.upload_file"),
                    variant="solid",
                    size="2",
                ),
                id="document_upload",
                multiple=True,
                on_drop=DocumentsListState.handle_upload(
                    rx.upload_files(
                        "document_upload",
                        on_upload_progress=DocumentsListState.handle_upload_progress,
                    )
                ),
            ),
            width="100%",
            align="center",
            spacing="2",
            # Trigger background fetch when component mounts
            on_mount=DocumentsListState.fetch_documents_on_mount,
        ),
        # Documents content
        _documents_content(),
        # Rename dialog
        _rename_document_dialog(),
        # Create note dialog
        _create_note_dialog(),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
        key=DocumentsListState.current_object_id,
    )


def documents_list_content() -> rx.Component:
    """Create the documents content without header.

    The header (title and action button) is managed at the tab level
    in the project detail page.

    :return: The documents content component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Documents content
        _documents_content(),
        # Rename dialog
        _rename_document_dialog(),
        # Create note dialog
        _create_note_dialog(),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
        key=DocumentsListState.current_object_id,
        # Trigger background fetch when component mounts
        on_mount=DocumentsListState.fetch_documents_on_mount,
    )


def _documents_content() -> rx.Component:
    """Create the documents content with cards and load more functionality.

    This component displays documents as cards
    with pagination support through a "Load More" button.

    :return: The documents content component
    :rtype: rx.Component
    """
    return rx.cond(
        DocumentsListState.pagination_state.is_loading
        & (DocumentsListState.pagination_state.documents.length() == 0),
        # Loading state - show spinner
        rx.center(
            rx.vstack(
                rx.spinner(size="3"),
                rx.text(
                    translate("documents_list.loading"), size="3", color="gray", margin_top="1rem"
                ),
                spacing="2",
                align="center",
            ),
            padding="3rem",
            width="100%",
            flex="1",
            min_height="0",
        ),
        rx.cond(
            DocumentsListState.pagination_state.documents.length() > 0,
            rx.vstack(
                # Document cards
                _documents_cards(),
                # Load more button
                rx.cond(
                    DocumentsListState.pagination_state.has_more,
                    rx.center(
                        rx.button(
                            rx.cond(
                                DocumentsListState.pagination_state.is_loading,
                                rx.hstack(
                                    rx.spinner(size="2"),
                                    translate("documents_list.loading_short"),
                                    spacing="2",
                                ),
                                rx.hstack(
                                    rx.icon("chevron-down", size=16),
                                    translate("documents_list.load_more"),
                                    spacing="2",
                                ),
                            ),
                            variant="soft",
                            size="2",
                            on_click=DocumentsListState.load_more_documents,
                            disabled=DocumentsListState.pagination_state.is_loading,
                        ),
                        width="100%",
                        padding="1rem",
                    ),
                ),
                width="100%",
                spacing="3",
                align_items="stretch",
                class_name="project-documents-component",
                # full height but not overflow parent
                flex="1",
                min_height="0",
                overflow_y="auto",
            ),
            # Empty state
            rx.center(
                rx.vstack(
                    rx.icon("folder-open", size=48, color="gray"),
                    rx.text(
                        translate("documents_list.empty_state"),
                        size="4",
                        color="gray",
                        margin_top="1rem",
                    ),
                    spacing="2",
                    align="center",
                ),
                padding="3rem",
                width="100%",
            ),
        ),
    )


def _documents_cards() -> rx.Component:
    """Create the documents card list.

    :return: The documents card list component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.foreach(DocumentsListState.pagination_state.documents, document_card),
        width="100%",
        spacing="2",
    )


def _rename_document_dialog() -> rx.Component:
    """Create the rename document dialog.

    :return: The rename dialog component
    :rtype: rx.Component
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(translate("documents_list.rename_dialog.title")),
            rx.dialog.description(
                translate("documents_list.rename_dialog.description"),
                size="2",
                margin_bottom="16px",
            ),
            rx.flex(
                rx.text(
                    translate("documents_list.rename_dialog.name_label"),
                    as_="div",
                    size="2",
                    margin_bottom="4px",
                    weight="bold",
                ),
                rx.input(
                    value=DocumentsListState.rename_document_name,
                    on_change=DocumentsListState.set_rename_document_name,
                    placeholder=translate("documents_list.rename_dialog.name_placeholder"),
                ),
                direction="column",
                spacing="3",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        translate("documents_list.rename_dialog.cancel"),
                        variant="soft",
                        color_scheme="gray",
                        on_click=DocumentsListState.close_rename_dialog,
                        disabled=DocumentsListState.is_renaming,
                    ),
                ),
                rx.button(
                    rx.cond(
                        DocumentsListState.is_renaming,
                        rx.hstack(
                            rx.spinner(size="2"),
                            translate("documents_list.rename_dialog.renaming"),
                            spacing="2",
                        ),
                        translate("documents_list.rename_dialog.submit"),
                    ),
                    on_click=DocumentsListState.handle_rename_document,
                    disabled=DocumentsListState.is_renaming,
                ),
                padding_top="16px",
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
            style={"max_width": 450},
            on_interact_outside=DocumentsListState.close_rename_dialog,
            on_escape_key_down=DocumentsListState.close_rename_dialog,
        ),
        open=DocumentsListState.rename_dialog_open,
    )


def _create_note_dialog() -> rx.Component:
    """Create the dialog for creating a new note.

    :return: The create note dialog component
    :rtype: rx.Component
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(translate("documents_list.create_note_dialog.title")),
            rx.form(
                rx.flex(
                    rx.text(
                        translate("documents_list.create_note_dialog.name_label"),
                        as_="div",
                        size="2",
                        margin_bottom="4px",
                        weight="bold",
                    ),
                    rx.input(
                        value=DocumentsListState.create_note_name,
                        on_change=DocumentsListState.set_create_note_name,
                        placeholder=translate("documents_list.create_note_dialog.name_placeholder"),
                        name="name",
                        required=True,
                    ),
                    direction="column",
                    spacing="3",
                ),
                rx.flex(
                    rx.dialog.close(
                        rx.button(
                            translate("documents_list.create_note_dialog.cancel"),
                            variant="soft",
                            color_scheme="gray",
                            type="button",
                            on_click=DocumentsListState.close_create_note_dialog,
                            disabled=DocumentsListState.is_creating_note,
                        ),
                    ),
                    rx.button(
                        rx.cond(
                            DocumentsListState.is_creating_note,
                            rx.hstack(
                                rx.spinner(size="2"),
                                translate("documents_list.create_note_dialog.creating"),
                                spacing="2",
                            ),
                            translate("documents_list.create_note_dialog.submit"),
                        ),
                        type="submit",
                        disabled=DocumentsListState.is_creating_note,
                    ),
                    padding_top="16px",
                    spacing="3",
                    margin_top="16px",
                    justify="end",
                ),
                on_submit=lambda _: DocumentsListState.handle_create_note(),
                reset_on_submit=False,
            ),
            style={"max_width": 450},
            on_interact_outside=DocumentsListState.close_create_note_dialog,
            on_escape_key_down=DocumentsListState.close_create_note_dialog,
        ),
        open=DocumentsListState.create_note_dialog_open,
    )
