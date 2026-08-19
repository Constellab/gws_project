from datetime import date, datetime

from gws_core import BaseModelDTO

from gws_project.task.task_dto import TaskPriority, TaskStatus


class MyDaySlotDTO(BaseModelDTO):
    """One planning slot of the signed-in user's day, in "My day".

    Project and parent task are denormalized here rather than looked up by the frontend,
    so one row of the screen is one object.
    """

    slot_id: str
    task_id: str
    task_title: str
    parent_task_title: str | None = None
    project_id: str
    project_title: str
    start_datetime: datetime
    end_datetime: datetime
    duration_minutes: int
    due_date: date | None = None
    is_overdue: bool = False
    # True when the slot is scheduled after the task's own due date. Only a screen that
    # reads slots and due dates together can surface this, which is half the point of it.
    is_scheduled_after_due: bool = False
    # Set only when the task's assignee is somebody else: the slot is mine, the
    # responsibility is not, and the row must say so rather than imply ownership.
    other_assignee_name: str | None = None


class MyRestTaskDTO(BaseModelDTO):
    """One task assigned to the signed-in user with no slot today, in "The rest"."""

    task_id: str
    title: str
    parent_task_title: str | None = None
    project_id: str
    project_title: str
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None = None
    is_overdue: bool = False
    # Start of the task's next slot after today, if any: the "scheduled Thu 9:00" badge.
    # Such a task stays in this list, it is only annotated.
    next_slot_start: datetime | None = None


class MyWorkDTO(BaseModelDTO):
    """Everything the My work screen shows for one user on one day.

    A derived view: no entity of its own, no field stored on the task. Every value here is
    computed from `Task.assign_to` and `PlanningSlot` on each read.
    """

    day: date
    day_slots: list[MyDaySlotDTO]
    rest_tasks: list[MyRestTaskDTO]
    planned_minutes: int
    daily_capacity_minutes: int
    is_over_capacity: bool
