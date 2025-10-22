"""Generic updatable chip component for displaying values with color-coded badges and update options."""

from enum import Enum
from typing import Callable, List, Literal

import reflex as rx


def updatable_chip(
    value: Enum,
    all_values: List[Enum],
    get_color_scheme: Callable[[Enum], str],
    size: Literal['1', '2', '3'] = None,
    on_value_change: Callable[[str], None] = None,
    allow_subtask: bool = False,
    readonly_message: str = "Value is calculated from children and cannot be updated manually."
) -> rx.Component:
    """Create a generic updatable chip component with color-coded badge and value selector.

    :param value: The current enum value
    :type value: Enum
    :param all_values: List of all possible enum values
    :type all_values: List[Enum]
    :param get_color_scheme: Function to get color scheme for a value
    :type get_color_scheme: Callable[[Enum], str]
    :param size: The badge size (optional)
    :type size: Literal['1', '2', '3']
    :param on_value_change: Callback function when value changes (optional)
    :type on_value_change: Callable[[str], None]
    :param allow_subtask: If True, shows readonly message instead of selector (optional)
    :type allow_subtask: bool
    :param readonly_message: Message to show when value cannot be updated (optional)
    :type readonly_message: str
    :return: The updatable chip component
    :rtype: rx.Component
    """
    badge = rx.badge(
        value,
        size=size,
        color_scheme=get_color_scheme(value),
        variant="soft",
        cursor="pointer" if on_value_change else "default",
    )

    # If no change handler, return just the badge
    if on_value_change is None:
        return badge

    # Create value option buttons
    value_options = []
    for value_option in all_values:
        value_options.append(
            rx.button(
                rx.badge(
                    value_option.value,
                    color_scheme=get_color_scheme(value_option),
                    variant="soft",
                ),
                on_click=lambda: on_value_change(value_option.name),
                variant="ghost",
                width="100%",
                cursor="pointer",
            )
        )

    # Return popover with value selector or info message
    return rx.popover.root(
        rx.popover.trigger(badge),
        rx.popover.content(
            rx.cond(
                allow_subtask,
                # Show message when task has subtasks
                rx.text(
                    readonly_message,
                    size="2",
                    color="gray",
                    max_width="150px"
                ),
                # Show value selector when task has no subtasks
                rx.flex(
                    *value_options,
                    direction="column",
                    spacing="2",
                    min_width="150px",
                ),
            ),
        ),
    )
