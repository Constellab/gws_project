"""Priority chip component for displaying task priority with color-coded badges."""

from typing import Literal

import reflex as rx
from gws_project.task.task_dto import TaskPriority


def priority_chip(priority: TaskPriority, size: Literal['1', '2', '3'] = None) -> rx.Component:
    """Create a priority chip component with color-coded badge.

    :param priority: The task priority (HIGH, MEDIUM, LOW)
    :type priority: TaskPriority
    :param size: The badge size (optional)
    :type size: Literal['1', '2', '3']
    :return: The priority chip component
    :rtype: rx.Component
    """

    return rx.badge(
        priority,
        size=size,
        color_scheme=rx.match(
            priority,
            (TaskPriority.HIGH, "red"),
            (TaskPriority.MEDIUM, "yellow"),
            "gray"
        ),
        variant="soft"
    )
