from gws_core import (
    Model,
    NullableCharField,
    TypedBooleanField,
    TypedEnumField,
    TypedForeignKeyField,
    TypedIntegerField,
)

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.task.task import Task
from gws_project.task_history.task_history_event_dto import TaskHistoryEventDTO
from gws_project.task_history.task_history_event_type import TaskHistoryEventType
from gws_project.user.user import User


class TaskHistoryEvent(Model):
    """
    TaskHistoryEvent model - Immutable audit trail entry for a single change made to a Task.

    Each row records one field change (or the task creation) with its old/new values
    stored language-neutral (see task_history_value): the sentence a user reads is built
    at display time, in their own language, from `event_type` and those values.
    """

    task = TypedForeignKeyField(Task, on_delete="CASCADE", backref="history_events")
    actor = TypedForeignKeyField(User, backref="+")
    event_type = TypedEnumField(choices=TaskHistoryEventType, max_length=30)
    old_value = NullableCharField(max_length=255)
    new_value = NullableCharField(max_length=255)
    # True when this entry was created by the automatic recalculation of a parent task
    # from its subtasks, rather than by a direct user action on this task.
    is_automatic = TypedBooleanField(default=False)
    # Global, strictly increasing counter used to order events chronologically. `created_at`
    # only has second precision, so several events created within the same request/second
    # (e.g. cascading recalculations up a task's ancestor chain) would otherwise tie.
    sequence = TypedIntegerField(default=0)

    _ICONS = {
        TaskHistoryEventType.CREATED: "sparkles",
        TaskHistoryEventType.TITLE_CHANGED: "pencil",
        TaskHistoryEventType.STATUS_CHANGED: "circle-dot",
        TaskHistoryEventType.PRIORITY_CHANGED: "flag",
        TaskHistoryEventType.DATES_CHANGED: "calendar",
        TaskHistoryEventType.ASSIGNEE_CHANGED: "user",
        TaskHistoryEventType.DESCRIPTION_UPDATED: "file-text",
        TaskHistoryEventType.MOVED: "move",
        TaskHistoryEventType.TYPE_CHANGED: "layers",
    }

    def get_icon(self) -> str:
        """The Lucide icon standing for this event's type.

        :return: The icon name
        :rtype: str
        """
        return self._ICONS[self.event_type]

    def to_dto(self) -> TaskHistoryEventDTO:
        """Convert the TaskHistoryEvent model to a TaskHistoryEventDTO for display in the frontend.

        :return: TaskHistoryEventDTO instance
        :rtype: TaskHistoryEventDTO
        """
        return TaskHistoryEventDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            task_id=self.task.id,
            actor=self.actor.to_dto(),
            event_type=self.event_type,
            old_value=self.old_value,
            new_value=self.new_value,
            is_automatic=self.is_automatic,
            icon=self.get_icon(),
        )

    class Meta:
        table_name = "gws_project_task_history_events"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
