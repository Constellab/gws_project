from datetime import date, datetime, time

from gws_core import SearchBuilder

from gws_project.planning.planning_slot import PlanningSlot
from gws_project.project.project import Project
from gws_project.task.task import Task


class PlanningSlotSearchBuilder(SearchBuilder):

    _task_joined: bool
    _project_joined: bool

    def __init__(self) -> None:
        super().__init__(PlanningSlot, default_orders=[PlanningSlot.start_datetime.asc()])
        self._task_joined = False
        self._project_joined = False

    def _ensure_task_join(self) -> None:
        if not self._task_joined:
            self.add_join(Task, on=(PlanningSlot.task == Task.id))
            self._task_joined = True

    def _ensure_project_join(self) -> None:
        self._ensure_task_join()
        if not self._project_joined:
            self.add_join(Project, on=(Task.project == Project.id))
            self._project_joined = True

    def add_week_range_filter(self, week_start: date, week_end: date) -> "PlanningSlotSearchBuilder":
        """Filter slots whose start_datetime falls within [week_start 00:00, week_end 23:59:59]."""
        start_dt = datetime.combine(week_start, time.min)
        end_dt = datetime.combine(week_end, time.max)
        self.add_expression(PlanningSlot.start_datetime.between(start_dt, end_dt))
        return self

    def add_project_filter(self, project_id: str) -> "PlanningSlotSearchBuilder":
        """Filter the search query by slots whose task belongs to a specific project."""
        self._ensure_task_join()
        self.add_expression(Task.project == project_id)
        return self

    def add_company_filter(self, company_id: str) -> "PlanningSlotSearchBuilder":
        """Filter the search query by slots whose task's project belongs to a specific company."""
        self._ensure_project_join()
        self.add_expression(Project.company == company_id)
        return self

    def add_user_filter(self, user_id: str) -> "PlanningSlotSearchBuilder":
        """Filter the search query by slots assigned to a specific user."""
        self.add_expression(PlanningSlot.assigned_user == user_id)
        return self

    def add_start_from_filter(self, from_datetime: datetime) -> "PlanningSlotSearchBuilder":
        """Filter the search query by slots starting at or after `from_datetime`.

        Used to find a person's upcoming slots (the "scheduled Thu 9:00" badge of the
        My work screen), where the horizon is open-ended rather than a fixed week.
        """
        self.add_expression(PlanningSlot.start_datetime >= from_datetime)
        return self
