from datetime import datetime

from gws_core import BaseModelDTO, ModelDTO, UserDTO

from gws_project.task.task_dto import TaskPriority


class CreatePlanningSlotDTO(BaseModelDTO):
    task_id: str
    assigned_user_id: str
    start_datetime: datetime
    end_datetime: datetime


class UpdatePlanningSlotDTO(BaseModelDTO):
    """Full desired state of a slot's assignment/time range.

    Used both when a slot is moved (person/day/time change, same duration) and when
    it is resized (duration changes): the caller always computes the full new
    start/end pair, so a single DTO covers both cases.
    """

    assigned_user_id: str
    start_datetime: datetime
    end_datetime: datetime


class PlanningSlotDTO(ModelDTO):
    """DTO for displaying a planning slot in the frontend.

    Project/company are resolved through the task (never re-entered on the slot).
    """

    task_id: str
    task_title: str
    task_priority: TaskPriority
    project_id: str
    project_title: str
    company_id: str | None
    company_name: str | None
    assigned_user: UserDTO
    start_datetime: datetime
    end_datetime: datetime


class PersonWeekLoadDTO(BaseModelDTO):
    """Computed weekly load of one person, for the capacity bar and overload banners."""

    user: UserDTO
    total_hours: float
    capacity_hours: float
    is_overloaded: bool
    daily_hours: dict[str, float]  # ISO date -> hours
    daily_capacity_hours: float
    overloaded_dates: list[str]  # ISO dates where daily capacity is exceeded


class SlotOverlapDTO(BaseModelDTO):
    """One pair of planning slots that overlap for the same person on the same day."""

    slot_a_id: str
    slot_b_id: str
    user_id: str
    user_name: str
    day: str  # ISO date
