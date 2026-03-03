import reflex as rx
from gws_reflex_main import extension_badge_component

from .documents_list_state import DocumentInfo, DocumentsListState


def document_card(document: DocumentInfo) -> rx.Component:
    """Create a card for a single document.

    :param document: The document info object
    :type document: DocumentInfo
    :return: The document card component
    :rtype: rx.Component
    """
    return rx.card(
        rx.hstack(
            # Left side: icon + document info
            rx.hstack(
                # File extension badge
                extension_badge_component(document.extension),
                # Document name and metadata
                rx.vstack(
                    rx.text(
                        document.name,
                        size="2",
                        weight="medium",
                        trim="both",
                        white_space="nowrap",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        width="100%",
                        padding_bottom="8px",
                    ),
                    rx.hstack(
                        rx.text(
                            document.size_pretty, size="1", color="var(--accent-9)", trim="both"
                        ),
                        rx.box(
                            width="3px",
                            height="3px",
                            border_radius="50%",
                            background="var(--accent-7)",
                            flex_shrink="0",
                        ),
                        rx.text(
                            document.last_modified, size="1", color="var(--accent-9)", trim="both"
                        ),
                        spacing="2",
                        align="center",
                    ),
                    spacing="0",
                    align_items="start",
                ),
                spacing="3",
                align="center",
                flex="1",
                min_width="0",
            ),
            # Right side: actions
            rx.hstack(
                rx.link(
                    rx.button(
                        rx.icon("external-link", size=14),
                        "Open",
                        variant="solid",
                        size="2",
                    ),
                    href=document.url,
                    is_external=True,
                ),
                _document_menu(document),
                spacing="2",
                align="center",
            ),
            width="100%",
            align="center",
            justify="between",
        ),
        width="100%",
        style={
            ":hover": {"background_color": "var(--gray-a2)"},
            "transition": "background 0.15s ease",
        },
    )


def _document_menu(document: DocumentInfo) -> rx.Component:
    """Create a dropdown menu for document actions.

    :param document: The document info object
    :type document: DocumentInfo
    :return: The menu component
    :rtype: rx.Component
    """
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("ellipsis-vertical", size=18),
                variant="ghost",
                size="2",
            ),
            margin_left="1em",
            margin_right="0",
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("download", size=14),
                "Download",
                on_click=DocumentsListState.handle_download_document(document.id, document.name),
            ),
            rx.menu.item(
                rx.icon("pencil", size=14),
                "Rename",
                on_click=DocumentsListState.open_rename_dialog(document.id, document.name),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash-2", size=14),
                "Delete",
                color="red",
                on_click=DocumentsListState.open_delete_document_dialog(document.id, document.name),
            ),
        ),
    )
