"""Bottom-of-sidebar block: current user summary + link to the Admin page."""

import reflex as rx
from gws_reflex_main import translate, user_profile_picture

from .project_app_router import ProjectAppRouter
from .sidebar_footer_state import SidebarFooterState


def sidebar_footer_component() -> rx.Component:
    """Create the sidebar footer with the current user's info and an Admin link.

    :return: The sidebar footer component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.divider(margin_y="0.25rem"),
        rx.cond(
            SidebarFooterState.current_user_dto,
            rx.hstack(
                user_profile_picture(SidebarFooterState.current_user_dto, size="normal"),
                rx.vstack(
                    rx.text(
                        SidebarFooterState.current_user_dto.first_name
                        + " "
                        + SidebarFooterState.current_user_dto.last_name,
                        size="2",
                        weight="medium",
                        line_height="1.1em",
                    ),
                    rx.text(
                        translate(SidebarFooterState.current_user_role_label_key),
                        size="1",
                        color="var(--gray-9)",
                    ),
                    spacing="0",
                    align_items="start",
                ),
                rx.spacer(),
                rx.link(
                    rx.icon("settings", size=18, color="var(--gray-9)"),
                    href=ProjectAppRouter.get_admin_url(),
                ),
                spacing="2",
                align="center",
                width="100%",
                padding="0 1rem",
            ),
        ),
        width="100%",
    )
