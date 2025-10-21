"""Common page layout component with left sidebar navigation menu."""

import reflex as rx


def page_layout(content: rx.Component) -> rx.Component:
    """Create a common page layout with left sidebar menu and main content area.

    This component provides a layout with:
    - Left sidebar: Navigation menu with links to Projects and Kanban
    - Main content area: The page content passed as parameter

    :param content: The main content to display
    :type content: rx.Component
    :return: The page layout component
    :rtype: rx.Component
    """
    return rx.hstack(
        # Left sidebar menu
        rx.vstack(
            rx.heading("Menu", size="6", margin_bottom="1rem"),

            # Navigation links
            rx.vstack(
                rx.link(
                    rx.hstack(
                        rx.icon("folder", size=20),
                        rx.text("Projects"),
                        spacing="2",
                        align="center"
                    ),
                    href="/",
                    width="100%",
                    padding="0.75rem 1rem",
                    border_radius="6px",
                    _hover={
                        "background": "var(--gray-3)",
                    },
                    color="inherit",
                    text_decoration="none",
                ),

                rx.link(
                    rx.hstack(
                        rx.icon("kanban", size=20),
                        rx.text("Kanban"),
                        spacing="2",
                        align="center"
                    ),
                    href="/kanban",
                    width="100%",
                    padding="0.75rem 1rem",
                    border_radius="6px",
                    _hover={
                        "background": "var(--gray-3)",
                    },
                    color="inherit",
                    text_decoration="none",
                ),

                width="100%",
                spacing="1",
                align_items="start"
            ),

            width="250px",
            min_width="250px",
            padding="1.5rem",
            background="var(--gray-2)",
            border_radius="8px",
            align_items="start",
            height="100vh",
            position="sticky",
            top="0",
        ),

        # Main content area
        rx.box(
            content,
            flex="1",
            width="100%",
            overflow_y="auto",
        ),

        width="100%",
        spacing="4",
        align_items="start",
    )
