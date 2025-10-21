"""Reflex wrapper for React Kanban board component using @dnd-kit."""

from typing import Any, Dict

import reflex as rx
from gws_core.core.model.model_dto import BaseModelDTO
from reflex.vars import Var

# Path to the custom JSX component
kanban_path = rx.asset("kanban_board.jsx", shared=True)
public_kanban_path = "$/public/" + kanban_path


class CardMoveEvent(BaseModelDTO):
    """Event data when a card is moved between columns.

    Attributes:
        new_board: The updated board state with all columns and cards
        card: The card that was moved
        source: The source column information
        destination: The destination column information
    """
    card_id: str
    from_column_id: str
    to_column_id: str


class KanbanBoard(rx.Component):
    """Custom Kanban Board component using @dnd-kit.

    A drag-and-drop Kanban board built with @dnd-kit/core and @dnd-kit/sortable.
    This component provides an accessible, keyboard-navigable Kanban interface.

    Example:
        ```python
        from custom_components.kanban import kanban_board

        kanban_board(
            board_data={
                "columns": [
                    {
                        "id": "TODO",
                        "title": "To Do",
                        "cards": [
                            {"id": "1", "title": "Task 1", "description": "Do something"}
                        ]
                    },
                    {
                        "id": "DOING",
                        "title": "In Progress",
                        "cards": []
                    }
                ]
            },
            on_card_move=MyState.handle_card_move,
        )
        ```
    """

    # Use the custom JSX component
    library = public_kanban_path
    tag = "KanbanBoard"

    # Component props
    board_data: Var[Dict[str, Any]]

    # Control whether columns can be dragged
    disable_column_drag: Var[bool]

    # Event handler for card movement
    on_card_move: rx.EventHandler[rx.event.passthrough_event_spec(dict)]


# Convenience function to create the component
kanban_board = KanbanBoard.create
