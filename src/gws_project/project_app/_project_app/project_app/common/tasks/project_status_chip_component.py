"""Status chip component for displaying project status with color-coded badges."""

from collections.abc import Callable
from typing import Literal

import reflex as rx
from gws_project.project.project_dto import ProjectStatus

from ..updatable_chip_component import updatable_chip


def _get_status_color(status: ProjectStatus):
    """Get the color scheme for a given status.

    :param status: The project status
    :type status: ProjectStatus
    :return: The color scheme name
    :rtype: str
    """
    return rx.match(status, (ProjectStatus.DRAFT, "gray"), (ProjectStatus.ACTIVE, "secondary"), (ProjectStatus.COMPLETED, "accent"), "gray")


def project_status_chip(
    status: ProjectStatus,
    size: Literal["1", "2", "3"] | None = None,
    on_status_change: Callable[[str], None] | None = None,
    show_icon: bool = False,
) -> rx.Component:
    """Create a status chip component with color-coded badge and status selector.

    :param status: The project status (DRAFT, ACTIVE, COMPLETED)
    :type status: ProjectStatus
    :param size: The badge size (optional)
    :type size: str
    :param on_status_change: Callback function when status changes (optional)
    :type on_status_change: Callable[[ProjectStatus], None]
    :param show_icon: If True, display a filled circle dot icon before the status text
    :type show_icon: bool
    :return: The status chip component
    :rtype: rx.Component
    """
    icon = rx.icon("circle", size=8, fill="currentColor") if show_icon else None

    return updatable_chip(
        value=status,
        all_values=list(ProjectStatus),
        get_color=_get_status_color,
        size=size,
        on_value_change=on_status_change,
        icon=icon,
    )
