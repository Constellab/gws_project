"""Common page layout component with left sidebar navigation menu."""

import reflex as rx


def menu_item(icon: str, label: str, href: str) -> rx.Component:
    """Create a menu item with icon and label.

    :param icon: The icon name (Lucide icon)
    :type icon: str
    :param label: The text label for the menu item
    :type label: str
    :param href: The URL to navigate to
    :type href: str
    :return: A menu item component
    :rtype: rx.Component
    """
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=20),
            rx.text(label),
            spacing="2",
            align="center"
        ),
        href=href,
        width="100%",
        padding="0.75rem 1rem",
        border_radius="6px",
        _hover={
            "background": "var(--gray-3)",
        },
        color="inherit",
        text_decoration="none",

    )


def page_layout(content: rx.Component, height: str = None, **kwargs) -> rx.Component:
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
            rx.hstack(
                rx.image(
                    src="/constellab-logo.svg",
                    height="2rem",
                    width="auto",
                ),
                rx.heading("Constellab project", size="6", line_height="1em"),
                spacing="4",
                align="center",
                margin_bottom="1rem",
            ),

            # Navigation links
            rx.vstack(
                menu_item("folder", "Projects", "/"),
                menu_item("kanban", "Kanban", "/kanban"),
                menu_item("layout_template", "Templates", "/templates"),
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
            height="100%",
            overflow_y="auto",
            padding="2em",
        ),

        width="100%",
        height=height,
        spacing="0",
        align_items="start",
        class_name="page-layout-container",
        **kwargs
    )
