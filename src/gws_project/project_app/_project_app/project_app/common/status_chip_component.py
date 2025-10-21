"""Status chip component for displaying task status with color-coded badges."""

from typing import Literal

import reflex as rx
from gws_project.task.task_dto import TaskStatus


def status_chip(status: TaskStatus, size: Literal['1', '2', '3'] = None) -> rx.Component:
    """Create a status chip component with color-coded badge.

    :param status: The task status (TODO, DOING, DONE)
    :type status: str
    :param size: The badge size (optional)
    :type size: str
    :return: The status chip component
    :rtype: rx.Component
    """

    return rx.badge(
        status,
        size=size,
        color_scheme=rx.match(
            status,
            (TaskStatus.DOING, "blue"),
            (TaskStatus.DONE, "green"),
            "gray"
        ),
        variant="soft"
    )
