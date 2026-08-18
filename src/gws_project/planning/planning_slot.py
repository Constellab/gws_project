from datetime import datetime

from gws_core import TypedDateTimeUTC, TypedForeignKeyField

from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.planning.planning_slot_dto import PlanningSlotDTO
from gws_project.task.task import Task
from gws_project.user.user import User


class PlanningSlot(ModelWithUser):
    """
    PlanningSlot model - A scheduled time interval (créneau) for one person on one task.

    A task can have several slots (scheduled several times, possibly for different
    people); a slot always belongs to exactly one task. Project and company are not
    duplicated here: they are always resolved through `task.project`/`task.project.company`.

    `assigned_user` is independent from `task.assign_to`: the task's `assign_to` is its
    official owner, while a slot's `assigned_user` is whoever is actually scheduled to do
    that occurrence of work (a task can be planned for several different people).
    """

    task = TypedForeignKeyField(Task, on_delete="CASCADE", backref="planning_slots")
    assigned_user = TypedForeignKeyField(User, backref="+")
    start_datetime = TypedDateTimeUTC()
    end_datetime = TypedDateTimeUTC()

    def duration_minutes(self) -> int:
        """Duration of the slot, in minutes."""
        return int((self.end_datetime - self.start_datetime).total_seconds() // 60)

    def overlaps_with(self, other: "PlanningSlot") -> bool:
        """Whether this slot's time interval overlaps with another slot's."""
        return self.start_datetime < other.end_datetime and other.start_datetime < self.end_datetime

    @classmethod
    def get_slots_of_task(cls, task_id: str) -> list["PlanningSlot"]:
        """Get all planning slots of a task, ordered by start time."""
        return list(cls.select().where(cls.task == task_id).order_by(cls.start_datetime))

    @classmethod
    def get_slots_between(cls, start: datetime, end: datetime) -> list["PlanningSlot"]:
        """Get all planning slots whose start_datetime falls within [start, end]."""
        return list(
            cls.select()
            .where((cls.start_datetime >= start) & (cls.start_datetime <= end))
            .order_by(cls.start_datetime)
        )

    def to_dto(self) -> PlanningSlotDTO:
        """Convert the PlanningSlot model to a PlanningSlotDTO for display in the frontend.

        Project and company are resolved through the task, never stored on the slot.
        """
        project = self.task.project
        company = project.company

        return PlanningSlotDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            task_id=self.task.id,
            task_title=self.task.title,
            task_priority=self.task.priority,
            project_id=project.id,
            project_title=project.title,
            company_id=company.id if company else None,
            company_name=company.name if company else None,
            assigned_user=self.assigned_user.to_dto(),
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime,
        )

    class Meta:
        table_name = "gws_project_planning_slots"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
