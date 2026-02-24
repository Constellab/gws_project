"""Project components for displaying project status."""

from collections.abc import Callable
from typing import Literal

import reflex as rx
from gws_project.project.project_dto import ProjectStatus

from ..updatable_chip_component import updatable_chip


def _get_project_status_color(status: ProjectStatus):
    """Get the color scheme for a given project status.

    :param status: The project status
    :type status: ProjectStatus
    :return: The color scheme name
    :rtype: str
    """
    return rx.match(
        status,
        (ProjectStatus.ACTIVE, "var(--secondary-9)"),
        (ProjectStatus.COMPLETED, "var(--accent-9)"),
        "var(--gray-4)",
    )


def project_status_chip(
    status: ProjectStatus,
    size: Literal["1", "2", "3"] | None = None,
    on_status_change: Callable[[str], None] | None = None,
) -> rx.Component:
    """Create a project status chip component with color-coded badge and status selector.

    :param status: The project status (DRAFT, ACTIVE, COMPLETED)
    :type status: ProjectStatus
    :param size: The badge size (optional)
    :type size: Literal['1', '2', '3']
    :param on_status_change: Callback function when status changes (optional)
    :type on_status_change: Callable[[str], None]
    :return: The project status chip component
    :rtype: rx.Component
    """
    return updatable_chip(
        value=status,
        all_values=list(ProjectStatus),
        get_color_scheme=_get_project_status_color,
        size=size,
        on_value_change=on_status_change,
    )


def project_status_badge(status: ProjectStatus, size: int = 8) -> rx.Component:
    """Create a colored dot indicating the project status.

    - COMPLETED: green (#10b981)
    - ACTIVE: orange (#F97316)
    - DRAFT: gray (#e2e8f0)

    :param status: The project status (DRAFT, ACTIVE, COMPLETED)
    :type status: ProjectStatus
    :param size: The dot diameter in pixels
    :type size: int
    :return: A colored dot component
    :rtype: rx.Component
    """
    color = rx.match(
        status,
        (ProjectStatus.COMPLETED, "var(--accent-9)"),
        (ProjectStatus.ACTIVE, "var(--secondary-9)"),
        "var(--gray-4)",
    )

    return rx.box(
        width=f"{size}px",
        height=f"{size}px",
        border_radius="50%",
        background=color,
        flex_shrink="0",
    )
