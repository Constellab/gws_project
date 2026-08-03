"""Reflex wrapper for React Kanban board component using @dnd-kit."""

from collections.abc import Callable

import reflex as rx
from gws_core import BaseModelDTO
from gws_core.apps.reflex._gws_reflex.gws_reflex_main.components.reflex_user_components import (
    get_user_color_mapping,
)
from gws_project.project.project_dto import ProjectDTO
from gws_project.task.task_dto import TaskDTO, TaskPriority, TaskStatus
from reflex.vars import Var

from ..status_colors import StatusColors
from ..tasks.task_priority_chip_component import PriorityColors

# Path to the custom TSX components
kanban_path = rx.asset("kanban_board.tsx", shared=True)
rx.asset("user_avatar.tsx", shared=True)
rx.asset("kanban_types.ts", shared=True)
rx.asset("kanban_utils.ts", shared=True)
rx.asset("priority_icon.tsx", shared=True)
rx.asset("sortable_card.tsx", shared=True)
rx.asset("kanban_column.tsx", shared=True)
rx.asset("add_card_row.tsx", shared=True)
public_kanban_path = "$/public/" + kanban_path


class CardDTO(BaseModelDTO):
    """DTO for a Kanban card.

    Attributes:
        id: Unique identifier for the card
        title: Card title
        description: Optional card description
        priority: Optional card priority
        assignee: Optional card assignee
        assignee_profile_picture_url: Optional URL for the assignee's profile picture
        parent_task_title: Optional parent task title
        is_leaf: Whether the task is a leaf task (no children)
        project_name: Optional project name
        start_date: Optional start date (ISO format string)
        end_date: Optional end date (ISO format string)
    """
    id: str
    title: str
    description: str | None = None
    priority: str | None = None
    assignee: str | None = None
    assignee_profile_picture_url: str | None = None
    parent_task_title: str | None = None
    is_leaf: bool = True
    project_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class ColumnDTO(BaseModelDTO):
    """DTO for a Kanban column.

    Attributes:
        id: Unique identifier for the column
        title: Column title
        cards: List of cards in this column
    """
    id: str
    title: str
    cards: list[CardDTO] = []


class BoardDataDTO(BaseModelDTO):
    """DTO for the Kanban board data structure.

    Attributes:
        columns: List of columns in the board
    """
    columns: list[ColumnDTO]


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

    # Mapping of column id (status) to CSS color prefix (e.g. {"TODO": "gray", "DOING": "secondary", "DONE": "tertiary"})
    status_color_map: Var[dict[str, str]]

    # Mapping of priority value to CSS color prefix (e.g. {"HIGH": "tertiary", "MEDIUM": "secondary", "LOW": "gray"})
    priority_color_map: Var[dict[str, str]]

    # Mapping of first name initial (A-Z) to hex color for user avatars
    user_color_map: Var[dict[str, str]]

    # Control whether columns can be dragged
    disable_column_drag: Var[bool]

    # Event handler for card movement
    on_card_move: rx.EventHandler[rx.event.passthrough_event_spec(dict)]

    # Event handler for card click
    on_card_click: rx.EventHandler[rx.event.passthrough_event_spec(str)]

    # ----- Inline "quick add task" row (no dialog), one column active at a time -----

    # Id of the column whose quick-add row is expanded ("" means none)
    quick_add_column_id: Var[str]
    quick_add_title: Var[str]
    quick_add_can_submit: Var[bool]
    quick_add_is_creating: Var[bool]

    # Destination browser panel: same folder-style browsing model as the Move Task
    # dialog (Projects -> a project's root tasks -> subtasks -> ...)
    quick_add_browse_open: Var[bool]
    quick_add_current_project_title: Var[str]
    quick_add_breadcrumb_tasks: Var[list[TaskDTO]]
    quick_add_projects: Var[list[ProjectDTO]]
    quick_add_tasks: Var[list[TaskDTO]]

    # Fired when the "+ Add task" trigger is clicked, with the column id
    on_quick_add_open: rx.EventHandler[rx.event.passthrough_event_spec(str)]
    # Fired when the quick-add row is cancelled (X button or Escape)
    on_quick_add_cancel: rx.EventHandler[rx.event.passthrough_event_spec()]
    # Fired on every keystroke in the title input
    on_quick_add_title_change: rx.EventHandler[rx.event.passthrough_event_spec(str)]
    # Fired when the "Choose project" chip is clicked
    on_quick_add_toggle_browse: rx.EventHandler[rx.event.passthrough_event_spec()]
    # Fired when navigating the destination browser: (kind, target_id). kind is one of
    # "projects_root", "project_root", "project", "task", "breadcrumb_task"
    on_quick_add_navigate: rx.EventHandler[rx.event.passthrough_event_spec(str, str)]
    # Fired when confirming the currently browsed level as the destination
    on_quick_add_select_here: rx.EventHandler[rx.event.passthrough_event_spec()]
    # Fired when submitting the new task (Add button or Enter key)
    on_quick_add_submit: rx.EventHandler[rx.event.passthrough_event_spec()]


STATUS_COLOR_MAP: dict[str, str] = {
    TaskStatus.BACKLOG.value: StatusColors.BACKLOG,
    TaskStatus.TODO.value: StatusColors.TODO,
    TaskStatus.DOING.value: StatusColors.ONGOING,
    TaskStatus.DONE.value: StatusColors.DONE,
}

PRIORITY_COLOR_MAP: dict[str, str] = {
    TaskPriority.HIGH.value: PriorityColors.HIGH,
    TaskPriority.MEDIUM.value: PriorityColors.MEDIUM,
    TaskPriority.LOW.value: PriorityColors.LOW,
}

USER_COLOR_MAP: dict[str, str] = get_user_color_mapping()

# Convenience function to create the component
kanban_board = KanbanBoard.create


def build_kanban_board_data(
    tasks: list[TaskDTO],
    task_to_card_converter: Callable[[TaskDTO], CardDTO],
    include_backlog: bool = False,
) -> BoardDataDTO:
    """Build kanban board data from a list of tasks.

    This utility function groups tasks by status and converts them to a kanban board format.

    :param tasks: List of tasks to convert
    :type tasks: List[TaskDTO]
    :param task_to_card_converter: Function to convert a TaskDTO to a CardDTO
    :type task_to_card_converter: Callable[[TaskDTO], CardDTO]
    :param include_backlog: Whether to include the Backlog column. Off by default so the
        board isn't cluttered with a column most users don't need to see.
    :type include_backlog: bool
    :return: BoardDataDTO with columns structure for the Kanban board
    :rtype: BoardDataDTO
    """
    # Group tasks by status
    todo_tasks = [task for task in tasks if task.status == TaskStatus.TODO]
    doing_tasks = [task for task in tasks if task.status == TaskStatus.DOING]
    done_tasks = [task for task in tasks if task.status == TaskStatus.DONE]

    columns = []

    if include_backlog:
        backlog_tasks = [task for task in tasks if task.status == TaskStatus.BACKLOG]
        columns.append(
            ColumnDTO(
                id=TaskStatus.BACKLOG.value,
                title="Backlog",
                cards=[task_to_card_converter(task) for task in backlog_tasks]
            )
        )

    columns.extend([
        ColumnDTO(
            id=TaskStatus.TODO.value,
            title="To Do",
            cards=[task_to_card_converter(task) for task in todo_tasks]
        ),
        ColumnDTO(
            id=TaskStatus.DOING.value,
            title="In Progress",
            cards=[task_to_card_converter(task) for task in doing_tasks]
        ),
        ColumnDTO(
            id=TaskStatus.DONE.value,
            title="Done",
            cards=[task_to_card_converter(task) for task in done_tasks]
        )
    ])

    return BoardDataDTO(columns=columns)
