import reflex as rx
from gws_core.space.space_dto import SpaceHierarchyObjectDTO

from .project_documents_state import ProjectDocumentsState


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
            ),
        ),
        rx.table.body(
            rx.foreach(
                ProjectDocumentsState.documents,
                lambda document: _document_row(document)
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
                _document_icon(document.objectType),
                rx.text(document.name),
                spacing="2",
                align="center"
            )
        ),
        rx.table.cell(
            rx.text(
                document.objectType,
                size="2",
                color="gray"
            )
        ),
        style={
            ":hover": {"background_color": "var(--gray-3)"},
            "cursor": "pointer"
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
