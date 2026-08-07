from gws_core import ModelDTO, UserDTO

from gws_project.task_history.task_history_event_type import (
    TaskHistoryEventType,
)


class TaskHistoryEventDTO(ModelDTO):
    """DTO for displaying a task history event in the frontend."""

    task_id: str
    actor: UserDTO
    event_type: TaskHistoryEventType
    old_value: str | None
    new_value: str | None
    is_automatic: bool
    # Pre-formatted server-side so the frontend never has to build the sentence,
    # pick an icon, or parse/reformat the timestamp itself
    message: str
    icon: str
    created_at_text: str
