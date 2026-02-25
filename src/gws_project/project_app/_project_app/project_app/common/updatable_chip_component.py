"""Generic updatable chip component for displaying values with color-coded badges and update options."""

from collections.abc import Callable
from enum import Enum
from typing import Literal

import reflex as rx


def updatable_chip(
    value: Enum,
    all_values: list[Enum],
    get_color: Callable[[Enum], str],
    size: Literal["1", "2", "3"] | None = None,
    on_value_change: Callable[[str], None] | None = None,
    allow_subtask: bool = False,
    readonly_message: str = "Value is calculated from children and cannot be updated manually.",
    get_icon: Callable[[Enum], rx.Component] | None = None,
) -> rx.Component:
    """Create a generic updatable chip component with color-coded badge and value selector.

    The get_color callback must return a CSS variable color prefix such as
    "accent", "secondary", "tertiary", or "gray". The chip then resolves
    the full CSS variable tokens (e.g. var(--accent-3), var(--accent-11)).

    :param value: The current enum value
    :type value: Enum
    :param all_values: List of all possible enum values
    :type all_values: List[Enum]
    :param get_color: Function returning a CSS variable prefix for a value
    :type get_color: Callable[[Enum], str]
    :param size: The badge size (optional)
    :type size: Literal['1', '2', '3']
    :param on_value_change: Callback function when value changes (optional)
    :type on_value_change: Callable[[str], None]
    :param allow_subtask: If True, shows readonly message instead of selector (optional)
    :type allow_subtask: bool
    :param readonly_message: Message to show when value cannot be updated (optional)
    :type readonly_message: str
    :param get_icon: Optional callback returning an icon component for each enum value.
        When provided, icons are shown on both the badge and the popover selection options.
    :type get_icon: Callable[[Enum], rx.Component] | None
    :return: The updatable chip component
    :rtype: rx.Component
    """

    icon = get_icon(value) if get_icon else None
    badge = _build_badge(value, get_color(value), size, icon, on_value_change)

    # If no change handler, return just the badge
    if on_value_change is None:
        return badge

    # Create value option buttons
    value_options = []
    for value_option in all_values:
        option_icon = get_icon(value_option) if get_icon else None
        value_options.append(
            rx.button(
                _build_badge(value_option.value, get_color(value_option), size, option_icon),
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
                rx.text(readonly_message, size="2", color="gray", max_width="150px"),
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


def _build_badge(
    value: Enum,
    color_prefix: str,
    size: Literal["1", "2", "3"] | None = None,
    icon: rx.Component | None = None,
    on_value_change: Callable[[str], None] | None = None,
) -> rx.Component:
    """Build a styled badge using CSS variable color tokens.

    :param value: The enum value to display
    :type value: Enum
    :param color_prefix: CSS variable prefix (e.g. "accent", "secondary", "tertiary", "gray")
    :type color_prefix: str
    :param size: The badge size
    :type size: Literal["1", "2", "3"] | None
    :param icon: Optional icon component
    :type icon: rx.Component | None
    :param on_value_change: Whether the badge is clickable
    :type on_value_change: Callable[[str], None] | None
    :return: The badge component
    :rtype: rx.Component
    """
    badge_children = []
    if icon:
        badge_children.append(icon)
    badge_children.append(rx.text(value, weight="bold", class_name="badge-text"))

    return rx.box(
        rx.hstack(
            *badge_children,
            spacing="1",
            align="center",
        ),
        background=f"var(--{color_prefix}-3)",
        color=f"var(--{color_prefix}-11)",
        padding="4px 10px" if size == "1" else "6px 12px",
        border_radius="99px",
        font_size="12px" if size == "1" else "14px",
        cursor="pointer" if on_value_change else "default",
        white_space="nowrap",
    )
