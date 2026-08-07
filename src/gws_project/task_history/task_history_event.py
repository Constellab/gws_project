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

    Each row records one field change (or the task creation) with the already-formatted
    old/new values, so the frontend never has to interpret raw enum/date/id values.
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

    def _build_assignee_message(self) -> str:
        """Build the message for an ASSIGNEE_CHANGED event.

        :return: The message describing the event
        :rtype: str
        """
        if not self.old_value:
            return f"assigned this task to {self.new_value}"
        if not self.new_value:
            return f"unassigned this task (was {self.old_value})"
        return f"changed assignee from {self.old_value} to {self.new_value}"

    def _build_message(self) -> str:
        """Build the human-readable, pre-formatted message describing this event.

        :return: The message describing the event
        :rtype: str
        """
        message_builders = {
            TaskHistoryEventType.CREATED: lambda: "created this task",
            TaskHistoryEventType.TITLE_CHANGED: (
                lambda: f'renamed this task from "{self.old_value}" to "{self.new_value}"'
            ),
            TaskHistoryEventType.STATUS_CHANGED: (
                lambda: f"changed status from {self.old_value} to {self.new_value}"
            ),
            TaskHistoryEventType.PRIORITY_CHANGED: (
                lambda: f"changed priority from {self.old_value} to {self.new_value}"
            ),
            TaskHistoryEventType.DATES_CHANGED: (
                lambda: f"changed the dates from {self.old_value} to {self.new_value}"
            ),
            TaskHistoryEventType.ASSIGNEE_CHANGED: self._build_assignee_message,
            TaskHistoryEventType.DESCRIPTION_UPDATED: lambda: "updated the description",
            TaskHistoryEventType.MOVED: (
                lambda: f"moved this task from {self.old_value} to {self.new_value}"
            ),
            TaskHistoryEventType.TYPE_CHANGED: (
                lambda: f"changed this task from {self.old_value} to {self.new_value}"
            ),
        }
        message = message_builders[self.event_type]()

        if self.is_automatic:
            message += " (automatically updated from subtasks)"

        return message

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
            message=self._build_message(),
            icon=self._ICONS[self.event_type],
            created_at_text=self.created_at.strftime("%b %d, %Y %H:%M"),
        )

    class Meta:
        table_name = "gws_project_task_history_events"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
