import reflex as rx

from .document_card_component import document_card
from .documents_list_state import DocumentInfo, DocumentsListState


def documents_list_view() -> rx.Component:
    """Create the documents view with header and content.

    :return: The documents view component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Documents header with upload button
        rx.hstack(
            rx.heading("Documents", size="4", weight="bold"),
            rx.spacer(),
            rx.upload.root(
                rx.button(
                    rx.spinner(loading=DocumentsListState.is_uploading),
                    rx.icon("upload", size=16),
                    "Upload File",
                    variant="soft",
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
            # Trigger background fetch when component mounts
            on_mount=DocumentsListState.fetch_documents_on_mount,
        ),
        # Documents content
        _documents_content(),
        # Rename dialog
        _rename_document_dialog(),
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
                rx.text("Loading documents...", size="3", color="gray", margin_top="1rem"),
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
                                    "Loading...",
                                    spacing="2",
                                ),
                                rx.hstack(
                                    rx.icon("chevron-down", size=16),
                                    "Load More",
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
                    rx.text("No documents found", size="4", color="gray", margin_top="1rem"),
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


def _documents_table() -> rx.Component:
    """Create the documents table.

    :return: The documents table component
    :rtype: rx.Component
    """
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Name"),
                rx.table.column_header_cell("Type"),
                rx.table.column_header_cell("Actions", justify="end"),
            ),
        ),
        rx.table.body(rx.foreach(DocumentsListState.pagination_state.documents, _document_row)),
        width="100%",
        variant="surface",
    )


def _document_row(document: DocumentInfo) -> rx.Component:
    """Create a table row for a single document.

    :param document: The document info object
    :type document: DocumentInfo
    :return: The document row component
    :rtype: rx.Component
    """
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                _document_icon(document.type), rx.text(document.name), spacing="2", align="center"
            )
        ),
        rx.table.cell(rx.text(document.type, size="2", color="gray")),
        rx.table.cell(
            rx.hstack(
                rx.link(
                    rx.button(
                        rx.icon("external-link", size=16),
                        "Open object",
                        variant="soft",
                        size="1",
                    ),
                    href=document.url,
                    is_external=True,
                ),
                spacing="2",
                align="center",
                justify="end",
                width="100%",
            )
        ),
        style={
            ":hover": {"background_color": "var(--gray-3)"},
        },
    )


def _document_icon(object_type) -> rx.Component:
    """Get the appropriate icon for a document based on its type.

    :param object_type: The object type enum value
    :return: The icon component
    :rtype: rx.Component
    """
    # Use rx.match to render different icon names based on the object type
    return rx.icon(
        rx.match(
            object_type,
            ("FOLDER", "folder"),
            ("NOTE", "file-text"),
            ("SCENARIO", "circle-play"),
            ("RESOURCE", "database"),
            ("CONSTELLAB_DOCUMENT", "file-text"),
            "file",  # Default for DOCUMENT and others
        ),
        size=16,
        color="gray",
        flex_shrink="0",
    )


def _rename_document_dialog() -> rx.Component:
    """Create the rename document dialog.

    :return: The rename dialog component
    :rtype: rx.Component
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Rename Document"),
            rx.dialog.description(
                "Enter a new name for the document.",
                size="2",
                margin_bottom="16px",
            ),
            rx.flex(
                rx.text(
                    "Document Name",
                    as_="div",
                    size="2",
                    margin_bottom="4px",
                    weight="bold",
                ),
                rx.input(
                    value=DocumentsListState.rename_document_name,
                    on_change=DocumentsListState.set_rename_document_name,
                    placeholder="Enter document name",
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
                        on_click=DocumentsListState.close_rename_dialog,
                        disabled=DocumentsListState.is_renaming,
                    ),
                ),
                rx.button(
                    rx.cond(
                        DocumentsListState.is_renaming,
                        rx.hstack(
                            rx.spinner(size="2"),
                            "Renaming...",
                            spacing="2",
                        ),
                        "Rename",
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
