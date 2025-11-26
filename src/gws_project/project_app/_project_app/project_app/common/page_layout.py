"""Common page layout component with left sidebar navigation menu."""

import reflex as rx
from gws_reflex_main import page_sidebar_component


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
        rx.hstack(rx.icon(icon, size=20), rx.text(label), spacing="2", align="center"),
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


def sidebar_content() -> rx.Component:
    """Create the sidebar content with logo and navigation links.

    :return: The sidebar content component
    :rtype: rx.Component
    """
    return rx.vstack(
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
            align_items="start",
        ),
        width="100%",
        align_items="start",
    )


def page_layout(
    content: rx.Component, header_content: rx.Component | None = None, height: str | None = None, **kwargs
) -> rx.Component:
    """Create a common page layout with left sidebar menu and main content area.

    This is a convenience wrapper around page_layout_component with the default sidebar content.

    :param content: The main content to display
    :type content: rx.Component
    :param header_content: Optional header content to display at the top (optional)
    :type header_content: rx.Component | None
    :param height: The height of the layout (optional)
    :type height: str | None
    :return: The page layout component
    :rtype: rx.Component
    """
    return page_sidebar_component(
        sidebar_content=sidebar_content(),
        content=content,
        header_content=header_content,
        height=height,
        **kwargs,
    )
