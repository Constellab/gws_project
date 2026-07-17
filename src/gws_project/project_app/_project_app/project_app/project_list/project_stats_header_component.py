"""Header component displaying project statistics cards."""

import reflex as rx
from gws_project.project.project_count_dto import ProjectCountDTO

from ..common.status_colors import StatusColors


def _stat_card(
    label: str,
    value: rx.Var[int],
    icon_name: str,
    accent_color: str,
) -> rx.Component:
    """Create a single statistics card.

    :param label: The label text below the value
    :type label: str
    :param value: The reactive value to display
    :type value: rx.Var[int]
    :param icon_name: The lucide icon name
    :type icon_name: str
    :param accent_color: The accent color for the icon background and value text
    :type accent_color: str
    :return: A stat card component
    :rtype: rx.Component
    """
    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(icon_name, size=20, color=accent_color),
                width="42px",
                height="42px",
                border_radius="12px",
                background=f"color-mix(in srgb, {accent_color} 12%, transparent)",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(
                    value.to(str),
                    size="5",
                    weight="bold",
                    color=accent_color,
                    line_height="1",
                    letter_spacing="-0.02em",
                ),
                rx.text(
                    label,
                    size="1",
                    color="var(--gray-9)",
                    weight="medium",
                ),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        background="var(--card-background)",
        border_radius="14px",
        padding="18px 20px",
        border="1px solid var(--gray-4)",
    )


def project_stats_header(project_count: rx.Var[ProjectCountDTO]) -> rx.Component:
    """Create the project statistics header with summary cards.

    Displays 4 cards: Total projects, Ongoing, Completed, and Not started.
    Mirrors the design from the example JSX stats cards section.

    :param project_count: The reactive project count DTO
    :type project_count: rx.Var[ProjectCountDTO]
    :return: The stats header component
    :rtype: rx.Component
    """
    return rx.grid(
        _stat_card(
            label="Total projects",
            value=project_count.total,
            icon_name="bar_chart_3",
            accent_color="var(--accent-9)",
        ),
        _stat_card(
            label="Ongoing",
            value=project_count.ongoing,
            icon_name="rocket",
            accent_color=StatusColors.css_var_ongoing(),
        ),
        _stat_card(
            label="Completed",
            value=project_count.done,
            icon_name="circle_check",
            accent_color=StatusColors.css_var_done(),
        ),
        _stat_card(
            label="Not started",
            value=project_count.todo,
            icon_name="clock",
            accent_color=StatusColors.css_var_todo(),
        ),
        columns="4",
        spacing="4",
        width="100%",
        display=["none", "none", "grid", "grid", "grid"],
    )
