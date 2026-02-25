"""Status chip component for displaying task status with color-coded badges."""

from collections.abc import Callable
from typing import Literal

import reflex as rx
from gws_project.task.task_dto import TaskStatus

from ..updatable_chip_component import updatable_chip


def _get_status_color(status: TaskStatus):
    """Get the color scheme for a given status.

    :param status: The task status
    :type status: TaskStatus
    :return: The color scheme name
    :rtype: str
    """
    return rx.match(status, (TaskStatus.DOING, "secondary"), (TaskStatus.DONE, "accent"), "gray")


def _get_status_icon(status: TaskStatus) -> rx.Component:
    """Get the icon component for a given status.

    :param status: The task status
    :type status: TaskStatus
    :return: The icon component
    :rtype: rx.Component
    """
    return rx.icon("circle", size=8, fill="currentColor")


def task_status_chip(
    status: TaskStatus,
    size: Literal["1", "2", "3"] | None = None,
    on_status_change: Callable[[str], None] | None = None,
    allow_subtask: bool = False,
) -> rx.Component:
    """Create a status chip component with color-coded badge and status selector.

    :param status: The task status (TODO, DOING, DONE)
    :type status: TaskStatus
    :param size: The badge size (optional)
    :type size: str
    :param on_status_change: Callback function when status changes (optional)
    :type on_status_change: Callable[[TaskStatus], None]
    :param allow_subtask: If True, shows message that status is calculated from children (optional)
    :type allow_subtask: bool
    :return: The status chip component
    :rtype: rx.Component
    """
    return updatable_chip(
        value=status,
        all_values=list(TaskStatus),
        get_color=_get_status_color,
        size=size,
        on_value_change=on_status_change,
        allow_subtask=allow_subtask,
        readonly_message="Status is calculated from children and cannot be updated manually.",
        get_icon=_get_status_icon,
    )
