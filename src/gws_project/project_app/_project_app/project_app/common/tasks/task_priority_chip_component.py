"""Priority chip component for displaying task priority with color-coded badges."""

from collections.abc import Callable
from typing import Literal

import reflex as rx
from gws_project.task.task_dto import TaskPriority

from ..updatable_chip_component import updatable_chip


def _get_priority_color(priority: TaskPriority):
    """Get the color scheme for a given priority.

    :param priority: The task priority
    :type priority: TaskPriority
    :return: The color scheme name
    :rtype: str
    """
    return rx.match(
        priority, (TaskPriority.HIGH, "tertiary"), (TaskPriority.MEDIUM, "secondary"), "gray"
    )


def _get_priority_icon(priority: TaskPriority) -> rx.Component:
    """Get the icon component for a given priority.

    :param priority: The task priority
    :type priority: TaskPriority
    :return: The icon component
    :rtype: rx.Component
    """
    icon_name = rx.match(
        priority,
        (TaskPriority.HIGH, "chevron-up"),
        (TaskPriority.MEDIUM, "minus"),
        "chevron-down",
    )
    return rx.icon(icon_name, size=12)


def task_priority_chip(
    priority: TaskPriority,
    size: Literal["1", "2", "3"] | None = None,
    on_priority_change: Callable[[str], None] | None = None,
    allow_subtask: bool = False,
) -> rx.Component:
    """Create a priority chip component with color-coded badge and priority selector.

    :param priority: The task priority (HIGH, MEDIUM, LOW)
    :type priority: TaskPriority
    :param size: The badge size (optional)
    :type size: Literal["1", "2", "3"] | None
    :param on_priority_change: Callback function when priority changes (optional)
    :type on_priority_change: Callable[[str], None] | None
    :param allow_subtask: If True, shows message that priority is calculated from children (optional)
    :type allow_subtask: bool
    :return: The priority chip component
    :rtype: rx.Component
    """
    return updatable_chip(
        value=priority,
        all_values=list(TaskPriority),
        get_color=_get_priority_color,
        size=size,
        on_value_change=on_priority_change,
        allow_subtask=allow_subtask,
        readonly_message="Priority is calculated from children and cannot be updated manually.",
        get_icon=_get_priority_icon,
    )
