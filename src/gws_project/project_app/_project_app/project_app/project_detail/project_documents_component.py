import reflex as rx
from gws_core.space.space_dto import SpaceHierarchyObjectDTO

from .project_documents_state import ProjectDocumentsState


def project_documents_view() -> rx.Component:
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
                    rx.spinner(loading=ProjectDocumentsState.is_uploading),
                    rx.icon("upload", size=16),
                    "Upload File",
                    variant="soft",
                    size="2",
                ),
                id="document_upload",
                multiple=True,
                on_drop=ProjectDocumentsState.handle_upload(
                    rx.upload_files("document_upload",
                                    on_upload_progress=ProjectDocumentsState.handle_upload_progress)
                ),
            ),
            width="100%",
            align="center"
        ),
        # Documents content
        project_documents_component(),
        # Rename dialog
        _rename_document_dialog(),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
    )


def project_documents_component() -> rx.Component:
    """Create the project documents component with a table and load more functionality.

    This component displays documents from the project's folder in a table format
    with pagination support through a "Load More" button.

    :return: The project documents component
    :rtype: rx.Component
    """
    return rx.cond(
        ProjectDocumentsState.documents.length() > 0,
        rx.vstack(
            # Table
            _documents_table(),
            # Load more button
            rx.cond(
                ProjectDocumentsState.has_more,
                rx.center(
                    rx.button(
                        rx.cond(
                            ProjectDocumentsState.is_loading,
                            rx.hstack(
                                rx.spinner(size="2"),
                                "Loading...",
                                spacing="2",
                            ),
                            rx.hstack(
                                rx.icon("chevron-down", size=16),
                                "Load More",
                                spacing="2",
                            )
                        ),
                        variant="soft",
                        size="2",
                        on_click=ProjectDocumentsState.load_more_documents,
                        disabled=ProjectDocumentsState.is_loading,
                    ),
                    width="100%",
                    padding="1rem",
                ),
            ),
            width="100%",
            spacing="0",
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
                    "No documents found",
                    size="4",
                    color="gray",
                    margin_top="1rem"
                ),
                spacing="2",
                align="center"
            ),
            padding="3rem",
            width="100%"
        )
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
                rx.table.column_header_cell("Actions"),
            ),
        ),
        rx.table.body(
            rx.foreach(
                ProjectDocumentsState.documents,
                _document_row
            )
        ),
        width="100%",
        variant="surface",
    )


def _document_row(document: SpaceHierarchyObjectDTO) -> rx.Component:
    """Create a table row for a single document.

    :param document: The document hierarchy object
    :type document: SpaceHierarchyObjectDTO
    :return: The document row component
    :rtype: rx.Component
    """
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                _document_icon(document.type),
                rx.text(document.name),
                spacing="2",
                align="center"
            )
        ),
        rx.table.cell(
            rx.text(
                document.type,
                size="2",
                color="gray"
            )
        ),
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
                _document_menu(document),
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
    # Use rx.match to render different icons based on the object type
    return rx.match(
        object_type,
        ("FOLDER", rx.icon("folder", size=16, color="gray")),
        ("NOTE", rx.icon("file-text", size=16, color="gray")),
        ("SCENARIO", rx.icon("circle-play", size=16, color="gray")),
        ("RESOURCE", rx.icon("database", size=16, color="gray")),
        ("CONSTELLAB_DOCUMENT", rx.icon("file-text", size=16, color="gray")),
        rx.icon("file", size=16, color="gray"),  # Default for DOCUMENT and others
    )


def _document_menu(document: SpaceHierarchyObjectDTO) -> rx.Component:
    """Create a dropdown menu for document actions.

    :param document: The document hierarchy object
    :type document: SpaceHierarchyObjectDTO
    :return: The menu component
    :rtype: rx.Component
    """
    return rx.menu.root(
        rx.menu.trigger(
            rx.icon_button(
                rx.icon("ellipsis-vertical", size=16),
                variant="ghost",
                size="1",
            )
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("download", size=14),
                "Download",
                on_click=ProjectDocumentsState.handle_download_document(document.id, document.name),
            ),
            rx.menu.item(
                rx.icon("pencil", size=14),
                "Rename",
                on_click=ProjectDocumentsState.open_rename_dialog(document.id, document.name),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash-2", size=14),
                "Delete",
                color="red",
                on_click=ProjectDocumentsState.open_delete_document_dialog(document.id, document.name),
            ),
        ),
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
                    value=ProjectDocumentsState.rename_document_name,
                    on_change=ProjectDocumentsState.set_rename_document_name,
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
                        on_click=ProjectDocumentsState.close_rename_dialog,
                        disabled=ProjectDocumentsState.is_renaming,
                    ),
                ),
                rx.button(
                    rx.cond(
                        ProjectDocumentsState.is_renaming,
                        rx.hstack(
                            rx.spinner(size="2"),
                            "Renaming...",
                            spacing="2",
                        ),
                        "Rename",
                    ),
                    on_click=ProjectDocumentsState.handle_rename_document,
                    disabled=ProjectDocumentsState.is_renaming,
                ),
                padding_top="16px",
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
            style={"max_width": 450},
        ),
        open=ProjectDocumentsState.rename_dialog_open,
    )
