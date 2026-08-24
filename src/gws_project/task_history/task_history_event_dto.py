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
    # The sentence is not pre-formatted either: the app builds it from `event_type`
    # and the values above, in the language of the reader (see the app's
    # common/tasks/task_history_message.py). Only the icon, which is language-neutral,
    # is decided here so both the timeline and the Home feed show the same one.
    icon: str
