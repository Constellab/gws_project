"""Small building blocks shared by the task and project details sidebars."""

import reflex as rx
from gws_reflex_main import translate, user_inline_component

from . import (
    details_sidebar_translations,  # noqa: F401  (side effect: registers translations)
)


def sidebar_section_label(label: str | rx.Var[str]) -> rx.Component:
    """Create a small uppercase gray label for a sidebar section.

    :param label: The label text
    :type label: str | rx.Var[str]
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


def sidebar_metadata_row(label: str | rx.Var[str], value: rx.Component) -> rx.Component:
    """Create a metadata row with a label on the left and value on the right.

    :param label: The label text
    :type label: str | rx.Var[str]
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


def sidebar_date_range(
    start_date_text: rx.Var[str], due_date_text: rx.Var[str]
) -> rx.Component:
    """Create the highlighted "start → due" box used by both sidebars.

    :param start_date_text: The pre-formatted start date
    :type start_date_text: rx.Var[str]
    :param due_date_text: The pre-formatted due date
    :type due_date_text: rx.Var[str]
    :return: The date range component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.text(
            rx.cond(start_date_text, start_date_text, "—"),
            size="2",
            weight="bold",
            color="var(--accent-9)",
        ),
        rx.text("→", size="2", color="gray"),
        rx.text(
            rx.cond(due_date_text, due_date_text, "—"),
            size="2",
            weight="bold",
            color="var(--accent-9)",
        ),
        background="var(--accent-2)",
        border_radius="12px",
        padding="12px 14px",
        align="center",
        spacing="3",
        width="100%",
    )


def sidebar_metadata_section(
    created_by: rx.Var,
    created_at_text: rx.Var[str],
    last_modified_by: rx.Var,
    last_modified_at_text: rx.Var[str],
) -> rx.Component:
    """Create the divider + "who created / modified this, and when" block.

    :param created_by: The creator UserDTO var
    :type created_by: rx.Var
    :param created_at_text: The pre-formatted creation timestamp
    :type created_at_text: rx.Var[str]
    :param last_modified_by: The last modifier UserDTO var
    :type last_modified_by: rx.Var
    :param last_modified_at_text: The pre-formatted last-modified timestamp
    :type last_modified_at_text: rx.Var[str]
    :return: The metadata section component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.divider(margin_bottom="0.5rem"),
        sidebar_metadata_row(
            translate("details_sidebar.created_by"),
            user_inline_component(created_by, size="small"),
        ),
        sidebar_metadata_row(
            translate("details_sidebar.created_at"),
            rx.text(created_at_text, size="1", weight="medium"),
        ),
        sidebar_metadata_row(
            translate("details_sidebar.last_modified_by"),
            user_inline_component(last_modified_by, size="small"),
        ),
        sidebar_metadata_row(
            translate("details_sidebar.last_modified_at"),
            rx.text(last_modified_at_text, size="1", weight="medium"),
        ),
        spacing="1",
        width="100%",
        padding_top="0.5rem",
    )
