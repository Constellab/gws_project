"""Reflex wrapper for React Kanban board component using @dnd-kit."""

from typing import List, Optional

import reflex as rx
from gws_core.core.model.model_dto import BaseModelDTO
from reflex.vars import Var

# Path to the custom TSX component
kanban_path = rx.asset("kanban_board.tsx", shared=True)
public_kanban_path = "$/public/" + kanban_path


class CardDTO(BaseModelDTO):
    """DTO for a Kanban card.

    Attributes:
        id: Unique identifier for the card
        title: Card title
        description: Optional card description
        priority: Optional card priority
        assignee: Optional card assignee
        parent_task_title: Optional parent task title
        is_leaf: Whether the task is a leaf task (no children)
        project_name: Optional project name
    """
    id: str
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    parent_task_title: Optional[str] = None
    is_leaf: bool = True
    project_name: Optional[str] = None


class ColumnDTO(BaseModelDTO):
    """DTO for a Kanban column.

    Attributes:
        id: Unique identifier for the column
        title: Column title
        cards: List of cards in this column
    """
    id: str
    title: str
    cards: List[CardDTO] = []


class BoardDataDTO(BaseModelDTO):
    """DTO for the Kanban board data structure.

    Attributes:
        columns: List of columns in the board
    """
    columns: List[ColumnDTO]


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

        # Default card rendering
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
            on_card_click=MyState.handle_card_click,
        )

        # With custom card template
        kanban_board(
            board_data=MyState.board_data,
            on_card_move=MyState.handle_card_move,
            on_card_click=MyState.handle_card_click,
            card_template={
                "title": lambda card: f"🎯 {card.title}",
                "description": lambda card: card.description.upper() if card.description else "",
            }
        )
        ```
    """

    # Use the custom JSX component
    library = public_kanban_path
    tag = "KanbanBoard"

    # Component props
    board_data: Var[BoardDataDTO]

    # Control whether columns can be dragged
    disable_column_drag: Var[bool]

    # Event handler for card movement
    on_card_move: rx.EventHandler[rx.event.passthrough_event_spec(dict)]

    # Event handler for card click
    on_card_click: rx.EventHandler[rx.event.passthrough_event_spec(str)]


# Convenience function to create the component
kanban_board = KanbanBoard.create
