from gws_core import CurrentUserService
from peewee import fn

from gws_project.task.task import Task
from gws_project.task_history.task_history_event import TaskHistoryEvent
from gws_project.task_history.task_history_event_type import TaskHistoryEventType


class TaskHistoryService:
    """Service class for logging and retrieving task history events."""

    def log(
        self,
        task: Task,
        event_type: TaskHistoryEventType,
        old_value: str | None = None,
        new_value: str | None = None,
        is_automatic: bool = False,
    ) -> TaskHistoryEvent:
        """Log a history event for a task.

        :param task: The task the event happened on
        :type task: Task
        :param event_type: The type of the event
        :type event_type: TaskHistoryEventType
        :param old_value: The pre-formatted previous value, if any
        :type old_value: Optional[str]
        :param new_value: The pre-formatted new value, if any
        :type new_value: Optional[str]
        :param is_automatic: True if this event was caused by the automatic recalculation
            of a parent task from its subtasks, rather than a direct user action
        :type is_automatic: bool
        :return: The created history event
        :rtype: TaskHistoryEvent
        """
        event = TaskHistoryEvent()
        event.task = task
        event.actor = CurrentUserService.get_and_check_current_user()
        event.event_type = event_type
        event.old_value = old_value
        event.new_value = new_value
        event.is_automatic = is_automatic
        event.sequence = self._get_next_sequence()
        event.save()
        return event

    def get_events_of_task(self, task_id: str) -> list[TaskHistoryEvent]:
        """Get all history events of a task, ordered from oldest to newest.

        :param task_id: The ID of the task
        :type task_id: str
        :return: List of history events
        :rtype: List[TaskHistoryEvent]
        """
        return list(
            TaskHistoryEvent.select()
            .where(TaskHistoryEvent.task == task_id)
            .order_by(TaskHistoryEvent.sequence)
        )

    def _get_next_sequence(self) -> int:
        """Get the next global sequence number to assign to a newly logged event.

        :return: The next sequence value
        :rtype: int
        """
        max_sequence = TaskHistoryEvent.select(fn.MAX(TaskHistoryEvent.sequence)).scalar()
        return (max_sequence or 0) + 1
