"""Common detail page layout component with header and main content."""

import reflex as rx


def detail_page_layout(
    main_content: rx.Component,
    header_content: rx.Component | None = None,
    header_right_content: rx.Component | None = None,
) -> rx.Component:
    """Create a common layout for detail pages with header and main content.

    The right sidebar is handled at the page_layout / page_sidebar_component level.
    This component only manages the left content column.

    :param main_content: The main content to display
    :type main_content: rx.Component
    :param header_content: Optional header content to display below the breadcrumb
    :type header_content: rx.Component | None
    :param header_right_content: Optional content to display on the right side of the header row
    :type header_right_content: rx.Component | None
    :return: The detail page layout component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Header row with optional right content
        rx.hstack(
            rx.spacer(),
            rx.cond(
                header_right_content is not None,
                header_right_content,
                rx.fragment(),
            ),
            width="100%",
            align_items="center",
        ),
        # Optional header content
        rx.cond(
            header_content is not None,
            rx.box(
                header_content,
                width="100%",
                padding_bottom="1rem",
            ),
            rx.fragment(),
        ),
        # Main content area
        rx.vstack(
            main_content,
            width="100%",
            flex="1",
            min_height="0",
        ),
        flex="1",
        width="100%",
    )
