import reflex as rx

from .breadcrumb.breadcrumb_component import breadcrumb_component


def detail_page_layout(
    main_content: rx.Component,
    sidebar_content: rx.Component
) -> rx.Component:
    """Create a common layout for detail pages with breadcrumb, main content and sidebar.

    This component provides a two-column layout with:
    - Breadcrumb: Positioned at the top, constrained by center layout max width
    - Center section: Main content with max width of 1000px, centered on large screens
    - Right section: Sidebar with fixed width of 450px, styled with background and padding

    :param breadcrumb: The breadcrumb navigation component
    :type breadcrumb: rx.Component
    :param main_content: The main content to display in the center section
    :type main_content: rx.Component
    :param sidebar_content: The sidebar content to display on the right
    :type sidebar_content: rx.Component
    :return: The detail page layout component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Two-column content layout
        rx.box(
            rx.hstack(
                # Main content area (center, max width 1000px)
                rx.box(
                    rx.box(breadcrumb_component(),
                           margin_bottom="1em"
                           ),
                    main_content,
                    max_width="1200px",
                    width="100%",
                    flex="1"
                ),

                # Sidebar (right, fixed width with styling)
                rx.vstack(
                    sidebar_content,
                    width="450px",
                    min_width="450px",
                    padding="1.5rem",
                    background="var(--gray-2)",
                    border_radius="8px",
                    align_items="start"
                ),

                width="100%",
                spacing="4",
                align_items="start",
                justify="center"
            ),
            width="100%"
        ),

        width="100%",
        spacing="4"
    )
