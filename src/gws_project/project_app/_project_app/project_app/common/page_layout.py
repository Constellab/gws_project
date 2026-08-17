"""Common page layout component with left sidebar navigation menu."""

import reflex as rx
from gws_reflex_main import (
    menu_item_component,
    page_sidebar_component,
    sidebar_menu_component,
    translate,
)

from . import sidebar_translations  # noqa: F401  (side effect: registers translations)
from .language_init_state import LanguageInitState
from .sidebar_footer_component import sidebar_footer_component


def sidebar_content() -> rx.Component:
    """Create the sidebar content with logo, navigation links, and a bottom
    footer showing the current user and a link to the Admin page.

    :return: The sidebar content component
    :rtype: rx.Component
    """
    nav = sidebar_menu_component(
        title="Project",
        subtitle="By Constellab",
        menu_items=[
            menu_item_component(
                "folder",
                translate("sidebar.projects"),
                "/",
                additional_active_route_prefixes=["/project"],
            ),
            menu_item_component("kanban", translate("sidebar.kanban"), "/kanban"),
            menu_item_component(
                "building-2",
                translate("sidebar.companies"),
                "/companies",
                additional_active_route_prefixes=["/company"],
            ),
            menu_item_component("gantt_chart", translate("sidebar.gantt"), "/gantt"),
            menu_item_component(
                "layout_template",
                translate("sidebar.templates"),
                "/templates",
                additional_active_route_prefixes=["/template"],
            ),
        ],
        logo_src="/constellab-logo.svg",
    )

    return rx.vstack(
        nav,
        sidebar_footer_component(),
        width="100%",
        height="100%",
        justify="between",
        align_items="start",
    )


def page_layout(
    content: rx.Component,
    header_content: rx.Component | None = None,
    height: str | None = None,
    right_sidebar_content: rx.Component | None = None,
    right_sidebar_width: str = "350px",
    max_content_width: str | None = None,
    **kwargs,
) -> rx.Component:
    """Create a common page layout with left sidebar menu and main content area.

    This is a convenience wrapper around page_layout_component with the default sidebar content.

    :param content: The main content to display
    :type content: rx.Component
    :param header_content: Optional header content to display at the top (optional)
    :type header_content: rx.Component | None
    :param height: The height of the layout (optional)
    :type height: str | None
    :param right_sidebar_content: Optional content for a right sidebar panel (optional)
    :type right_sidebar_content: rx.Component | None
    :param right_sidebar_width: The width of the right sidebar (default: "350px")
    :type right_sidebar_width: str
    :param max_content_width: Optional max width to constrain header and content area (optional)
    :type max_content_width: str | None
    :return: The page layout component
    :rtype: rx.Component
    """
    caller_on_mount = kwargs.pop("on_mount", None)
    on_mount = (
        [LanguageInitState.ensure_default_language, caller_on_mount]
        if caller_on_mount is not None
        else LanguageInitState.ensure_default_language
    )

    return page_sidebar_component(
        sidebar_content=sidebar_content(),
        content=content,
        header_content=header_content,
        height=height,
        right_sidebar_content=right_sidebar_content,
        right_sidebar_width=right_sidebar_width,
        max_content_width=max_content_width,
        on_mount=on_mount,
        **kwargs,
    )
