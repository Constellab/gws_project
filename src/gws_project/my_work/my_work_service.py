from datetime import date, datetime, time, timedelta

from gws_core import BadRequestException, CurrentUserService

from gws_project.core.working_hours_service import WorkingHoursService
from gws_project.my_work.my_work_dto import MyDaySlotDTO, MyRestTaskDTO, MyWorkDTO
from gws_project.planning.planning_slot import PlanningSlot
from gws_project.planning.planning_slot_dto import CreatePlanningSlotDTO
from gws_project.planning.planning_slot_service import (
    DEFAULT_SLOT_DURATION_MINUTES,
    PlanningSlotService,
)
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskPriority, TaskStatus
from gws_project.task.task_search_builder import TaskSearchBuilder
from gws_project.task.task_service import TaskService
from gws_project.user.user import User


class MyWorkService:
    """Service backing the "My work" screen: a personal, cross-project reading of what the
    signed-in user has to do today and what comes next.

    It introduces no data of its own. Both lists are derived on every read:

    - "My day" comes from `PlanningSlot.assigned_user` (who spends time on it),
    - "The rest" comes from `Task.assign_to` (who is responsible for it),

    and a task appears in exactly one of them.

    The view is strictly personal. None of these methods takes a user id: the user is always
    resolved server-side from the session, which is what makes it impossible - for an
    administrator as much as for anyone else - to read somebody else's day through this
    service.
    """

    # "The rest" is ordered by urgency, not by priority first: a low-priority task due
    # yesterday is more pressing than a high-priority one due next month.
    _PRIORITY_RANK = {TaskPriority.HIGH: 0, TaskPriority.MEDIUM: 1, TaskPriority.LOW: 2}

    def get_my_work(self, day: date | None = None) -> MyWorkDTO:
        """Build both lists of the My work screen for the signed-in user.

        :param day: The day to read, defaults to today.
        :type day: date | None
        """
        day = day or date.today()
        user = self._get_current_user()
        settings = WorkingHoursService.get_settings()
        slot_service = PlanningSlotService()

        day_slots = slot_service.get_slots_for_day(day, user.id)
        day_slot_dtos = [self._to_day_slot_dto(slot, user, day) for slot in day_slots]

        # A task appears exactly once: having a slot today puts it in "My day", and a task
        # in "My day" is never repeated in "The rest".
        scheduled_today_task_ids = {slot.task.id for slot in day_slots}

        next_slot_by_task = self._get_next_slot_start_by_task(user, day, slot_service)
        rest_task_dtos = [
            self._to_rest_task_dto(task, next_slot_by_task.get(task.id), day)
            for task in self._get_rest_tasks(user, scheduled_today_task_ids)
        ]
        rest_task_dtos.sort(key=self._rest_sort_key)

        planned_minutes = sum(dto.duration_minutes for dto in day_slot_dtos)
        daily_capacity_minutes = int(round(slot_service.daily_capacity_hours(settings) * 60))

        return MyWorkDTO(
            day=day,
            day_slots=day_slot_dtos,
            rest_tasks=rest_task_dtos,
            planned_minutes=planned_minutes,
            daily_capacity_minutes=daily_capacity_minutes,
            is_over_capacity=daily_capacity_minutes > 0 and planned_minutes > daily_capacity_minutes,
            can_add_to_day=slot_service.find_first_free_start(
                day, DEFAULT_SLOT_DURATION_MINUTES, settings, day_slots
            )
            is not None,
        )

    def reorder_my_day(self, ordered_slot_ids: list[str], day: date | None = None) -> MyWorkDTO:
        """Reorder the signed-in user's day, and return the refreshed screen.

        The reordering rewrites the slots' start/end times, so it shows up on the team
        Planning grid straight away - there is no personal ordering kept on the side.
        """
        day = day or date.today()
        user = self._get_current_user()
        settings = WorkingHoursService.get_settings()

        PlanningSlotService().reorder_day_slots(day, user.id, ordered_slot_ids, settings)

        return self.get_my_work(day)

    def add_to_my_day(self, task_id: str, day: date | None = None) -> MyDaySlotDTO:
        """Ask the Planning for a slot on `day`, at the first free time range.

        My work never creates a slot at an arbitrary time: it asks for the first opening
        inside the working hours and lets the Planning own the result.

        :raises BadRequestException: if the working day has no room left. My work refuses
            rather than appending after the end of the day: a slot at 2am is not a heavier
            day, it is wrong data on the team Planning, and rearranging a full day is a
            Planning job.
        :return: the created slot
        :rtype: MyDaySlotDTO
        """
        day = day or date.today()
        user = self._get_current_user()
        task = TaskService().get_task(task_id)

        if task.assign_to.id != user.id:
            raise BadRequestException("Only the assignee of a task can add it to their day.")
        if task.status in (TaskStatus.BACKLOG, TaskStatus.DONE):
            raise BadRequestException(
                "A backlog or completed task cannot be added to your day."
            )
        if task.allow_subtasks:
            raise BadRequestException(
                "Schedule the subtasks rather than their parent task, whose status is derived."
            )

        settings = WorkingHoursService.get_settings()
        slot_service = PlanningSlotService()
        start_datetime = slot_service.find_first_free_start(
            day,
            DEFAULT_SLOT_DURATION_MINUTES,
            settings,
            slot_service.get_slots_for_day(day, user.id),
        )

        if start_datetime is None:
            raise BadRequestException(
                "Your working day is already full. Rearrange today's schedule from the "
                "Planning instead."
            )

        slot = slot_service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task_id,
                assigned_user_id=user.id,
                start_datetime=start_datetime,
                end_datetime=start_datetime + timedelta(minutes=DEFAULT_SLOT_DURATION_MINUTES),
            )
        )

        return self._to_day_slot_dto(slot, user, day)

    def _get_current_user(self) -> User:
        """The signed-in user, as the brick's local mirror of the gws_core user.

        Both share the same primary key (see `User.from_gws_core_user`), so the id can be
        carried straight from one to the other.
        """
        core_user = CurrentUserService.get_and_check_current_user()
        return User.get_by_id_and_check(core_user.id)

    def _get_rest_tasks(self, user: User, scheduled_today_task_ids: set[str]) -> list[Task]:
        """Unfinished tasks assigned to the user with no slot today.

        Excluded, in order: projects the user is no longer a member of, parent tasks
        (`allow_subtasks`), the backlog, done tasks, subtasks of a backlogged parent, and
        anything already scheduled today.
        """
        project_ids = [project.id for project in ProjectService().get_current_user_projects()]
        if not project_ids:
            # Return early rather than skip the filter: an empty `IN ()` list would widen the
            # query to every task of the lab instead of narrowing it to none.
            return []

        search_builder = TaskSearchBuilder()
        search_builder.add_projects_filter(project_ids)
        search_builder.add_user_filter(user.id)
        # Parent tasks have a status derived from their children, so they cannot be ticked
        # off; their assigned subtasks show up here instead.
        search_builder.add_allow_subtasks_filter(False)
        search_builder.add_exclude_status_filter(TaskStatus.BACKLOG)
        search_builder.add_exclude_status_filter(TaskStatus.DONE)
        # The backlog is not a commitment, and neither are the subtasks of a backlogged task.
        search_builder.add_exclude_backlog_parent_filter()

        return [
            task for task in search_builder.search_all()
            if task.id not in scheduled_today_task_ids
        ]

    def _get_next_slot_start_by_task(
        self,
        user: User,
        day: date,
        slot_service: PlanningSlotService,
    ) -> dict[str, datetime]:
        """Start of each task's next slot for this user, strictly after `day`.

        The horizon starts the following day on purpose: a task with a slot later today is
        already in "My day", so it needs no "scheduled later" badge.
        """
        tomorrow = datetime.combine(day + timedelta(days=1), time.min)

        next_slot_start: dict[str, datetime] = {}
        for slot in slot_service.get_upcoming_slots_for_user(user.id, tomorrow):
            # Slots come back ordered by start time, so the first one seen is the earliest.
            next_slot_start.setdefault(slot.task.id, slot.start_datetime)

        return next_slot_start

    def _to_day_slot_dto(self, slot: PlanningSlot, user: User, day: date) -> MyDaySlotDTO:
        task = slot.task
        due_date = task.due_date

        return MyDaySlotDTO(
            slot_id=slot.id,
            task_id=task.id,
            task_title=task.title,
            parent_task_title=task.parent_task.title if task.parent_task else None,
            project_id=task.project.id,
            project_title=task.project.title,
            start_datetime=slot.start_datetime,
            end_datetime=slot.end_datetime,
            duration_minutes=slot.duration_minutes(),
            due_date=due_date,
            is_overdue=due_date is not None and due_date < day,
            is_scheduled_after_due=due_date is not None and slot.start_datetime.date() > due_date,
            other_assignee_name=(
                self._format_user(task.assign_to) if task.assign_to.id != user.id else None
            ),
        )

    def _to_rest_task_dto(
        self,
        task: Task,
        next_slot_start: datetime | None,
        day: date,
    ) -> MyRestTaskDTO:
        due_date = task.due_date

        return MyRestTaskDTO(
            task_id=task.id,
            title=task.title,
            parent_task_title=task.parent_task.title if task.parent_task else None,
            project_id=task.project.id,
            project_title=task.project.title,
            status=task.status,
            priority=task.priority,
            due_date=due_date,
            is_overdue=due_date is not None and due_date < day,
            next_slot_start=next_slot_start,
        )

    @classmethod
    def _rest_sort_key(cls, dto: MyRestTaskDTO) -> tuple:
        """Overdue first, then due date ascending (undated last), then priority."""
        return (
            not dto.is_overdue,
            dto.due_date or date.max,
            cls._PRIORITY_RANK.get(dto.priority, len(cls._PRIORITY_RANK)),
        )

    def _format_user(self, user: User) -> str:
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name or user.email
