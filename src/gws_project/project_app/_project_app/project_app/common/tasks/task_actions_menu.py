"""Actions menu component for tasks."""

from collections.abc import Callable

import reflex as rx


def task_actions_menu(
    on_update: rx.EventHandler | Callable,
    on_delete: rx.EventHandler | Callable,
    on_change_type: rx.EventHandler | Callable | None = None,
    stop_propagation: bool = False,
    **kwargs,
) -> rx.Component:
    """Create the actions menu for a task.

    :param on_update: Event handler for the update action
    :type on_update: rx.EventHandler | Callable
    :param on_delete: Event handler for the delete action
    :type on_delete: rx.EventHandler | Callable
    :param on_change_type: Event handler for the change type action
    :type on_change_type: rx.EventHandler | Callable | None
    :param stop_propagation: Whether to stop event propagation (useful in table rows)
    :type stop_propagation: bool
    :return: The actions menu component
    :rtype: rx.Component
    """
    update_click = [rx.stop_propagation, on_update] if stop_propagation else on_update
    delete_click = [rx.stop_propagation, on_delete] if stop_propagation else on_delete

    menu_items = [
        rx.menu.item(
            rx.icon("pencil", size=16),
            "Update",
            on_click=update_click,
        ),
    ]

    if on_change_type:
        change_type_click = (
            [rx.stop_propagation, on_change_type] if stop_propagation else on_change_type
        )
        menu_items.append(
            rx.menu.item(
                rx.icon("arrow-left-right", size=16),
                "Change task type",
                on_click=change_type_click,
            )
        )

    menu_items.append(rx.menu.separator())
    menu_items.append(
        rx.menu.item(
            rx.icon("trash-2", size=16),
            "Delete",
            color_scheme="red",
            on_click=delete_click,
        )
    )

    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("ellipsis-vertical", size=18),
                variant="ghost",
                size="2",
            ),
            # this is to make the size of the parent correct
            margin_left="0",
            **kwargs,
        ),
        rx.menu.content(*menu_items),
    )
