from datetime import date, datetime, time, timedelta

from gws_core import BadRequestException, NotFoundException

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.core.working_hours_settings import WorkingHoursSettings
from gws_project.planning.planning_slot import PlanningSlot
from gws_project.planning.planning_slot_dto import (
    CreatePlanningSlotDTO,
    PersonWeekLoadDTO,
    SlotOverlapDTO,
    UpdatePlanningSlotDTO,
)
from gws_project.planning.planning_slot_search_builder import PlanningSlotSearchBuilder
from gws_project.project.project_security_service import ProjectSecurityService, ProjectUserRole
from gws_project.user.user import User


class PlanningSlotService:
    """Service managing planning slots (créneaux): CRUD, week duplication, and the
    capacity/overlap computations backing the Planning screen's load bars and banners.

    Planning is indicative, never blocking: none of these methods reject a slot for
    overloading a person or overlapping another slot, they only expose that
    information for the frontend to display as (dismissible) warnings.
    """

    def get_slots_for_week(
        self,
        week_start: date,
        project_id: str | None = None,
        company_id: str | None = None,
        user_id: str | None = None,
    ) -> list[PlanningSlot]:
        """Get all planning slots starting within the 7-day week starting at `week_start`."""
        week_end = week_start + timedelta(days=6)

        search_builder = PlanningSlotSearchBuilder()
        search_builder.add_week_range_filter(week_start, week_end)
        if project_id:
            search_builder.add_project_filter(project_id)
        if company_id:
            search_builder.add_company_filter(company_id)
        if user_id:
            search_builder.add_user_filter(user_id)

        return search_builder.search_all()

    def get_slot(self, slot_id: str) -> PlanningSlot:
        """Get a planning slot by id, checking the current user has access to its task's project."""
        slot = PlanningSlot.get_by_id(slot_id)
        if not slot:
            raise NotFoundException("Planning slot not found")

        ProjectSecurityService().get_and_check_role_for_task(slot.task.id, ProjectUserRole.USER)

        return slot

    @ProjectDbManager.transaction()
    def create_slot(self, dto: CreatePlanningSlotDTO) -> PlanningSlot:
        """Create a planning slot for a task and a person.

        No check that `assigned_user` is a member of the task's project: planning is
        indicative and a planner may need to schedule anyone against any task.
        """
        self._validate_time_range(dto.start_datetime, dto.end_datetime)

        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(dto.task_id, ProjectUserRole.USER)
        assigned_user = User.get_by_id_and_check(dto.assigned_user_id)

        slot = PlanningSlot()
        slot.task = task
        slot.assigned_user = assigned_user
        slot.start_datetime = dto.start_datetime
        slot.end_datetime = dto.end_datetime
        slot.save()

        return slot

    @ProjectDbManager.transaction()
    def update_slot(self, slot_id: str, dto: UpdatePlanningSlotDTO) -> PlanningSlot:
        """Update a slot's person and/or time range.

        A single method covers both "move" (person/day/time changed, same duration)
        and "resize" (only start or only end changed): the caller always sends the
        full desired start/end pair.
        """
        self._validate_time_range(dto.start_datetime, dto.end_datetime)

        slot = self.get_slot(slot_id)
        slot.assigned_user = User.get_by_id_and_check(dto.assigned_user_id)
        slot.start_datetime = dto.start_datetime
        slot.end_datetime = dto.end_datetime
        slot.save()

        return slot

    @ProjectDbManager.transaction()
    def delete_slot(self, slot_id: str) -> None:
        """Delete a planning slot."""
        slot = self.get_slot(slot_id)
        slot.delete_instance()

    @ProjectDbManager.transaction()
    def duplicate_week(
        self,
        source_week_start: date,
        target_week_start: date,
        user_ids: list[str] | None = None,
    ) -> list[PlanningSlot]:
        """Duplicate planning slots of the source week into the target week.

        Copied fields: task, assigned_user, and the time range shifted by the exact
        number of days between the two week starts (normally 7). Not copied: id,
        created_by/created_at (the duplicate is a fresh row owned by the current user).

        :param user_ids: If given, only slots assigned to one of these user ids are
            duplicated (lets the caller offer a person-by-person selection); if None,
            every slot of the source week is duplicated.
        """
        source_week_end = source_week_start + timedelta(days=6)
        source_slots = PlanningSlot.get_slots_between(
            datetime.combine(source_week_start, time.min),
            datetime.combine(source_week_end, time.max),
        )

        if user_ids is not None:
            user_id_set = set(user_ids)
            source_slots = [slot for slot in source_slots if slot.assigned_user.id in user_id_set]

        shift = target_week_start - source_week_start

        new_slots = []
        for source_slot in source_slots:
            new_slot = PlanningSlot()
            new_slot.task = source_slot.task
            new_slot.assigned_user = source_slot.assigned_user
            new_slot.start_datetime = source_slot.start_datetime + shift
            new_slot.end_datetime = source_slot.end_datetime + shift
            new_slot.save()
            new_slots.append(new_slot)

        return new_slots

    def compute_week_loads(
        self,
        slots: list[PlanningSlot],
        people: list[User],
        settings: WorkingHoursSettings,
    ) -> list[PersonWeekLoadDTO]:
        """Compute each person's total/daily load for the given slots against the
        single, app-wide working hours settings (capacity is uniform across people)."""
        daily_capacity_hours = self._daily_capacity_hours(settings)
        capacity_hours = settings.weekly_hours

        loads = []
        for person in people:
            daily_hours: dict[str, float] = {}
            for slot in slots:
                if slot.assigned_user.id != person.id:
                    continue
                day_key = slot.start_datetime.date().isoformat()
                daily_hours[day_key] = daily_hours.get(day_key, 0.0) + slot.duration_minutes() / 60

            total_hours = sum(daily_hours.values())
            overloaded_dates = sorted(day for day, hours in daily_hours.items() if hours > daily_capacity_hours)

            loads.append(
                PersonWeekLoadDTO(
                    user=person.to_dto(),
                    total_hours=round(total_hours, 2),
                    capacity_hours=capacity_hours,
                    is_overloaded=total_hours > capacity_hours,
                    daily_hours={day: round(hours, 2) for day, hours in daily_hours.items()},
                    daily_capacity_hours=round(daily_capacity_hours, 2),
                    overloaded_dates=overloaded_dates,
                )
            )

        return loads

    def compute_overlaps(self, slots: list[PlanningSlot]) -> list[SlotOverlapDTO]:
        """Detect every pair of slots assigned to the same person on the same day
        whose time ranges overlap."""
        groups: dict[tuple[str, str], list[PlanningSlot]] = {}
        for slot in slots:
            key = (slot.assigned_user.id, slot.start_datetime.date().isoformat())
            groups.setdefault(key, []).append(slot)

        overlaps: list[SlotOverlapDTO] = []
        for (user_id, day), group_slots in groups.items():
            ordered = sorted(group_slots, key=lambda s: s.start_datetime)
            for i, slot_a in enumerate(ordered):
                for slot_b in ordered[i + 1:]:
                    if slot_a.overlaps_with(slot_b):
                        overlaps.append(
                            SlotOverlapDTO(
                                slot_a_id=slot_a.id,
                                slot_b_id=slot_b.id,
                                user_id=user_id,
                                user_name=self._format_user(slot_a.assigned_user),
                                day=day,
                            )
                        )

        return overlaps

    def _validate_time_range(self, start_datetime: datetime, end_datetime: datetime) -> None:
        if end_datetime <= start_datetime:
            raise BadRequestException("A planning slot's end time must be after its start time.")

    def _daily_capacity_hours(self, settings: WorkingHoursSettings) -> float:
        """Length of a working day minus the lunch break, in hours.

        Admin's working-hours form does not enforce non-empty/well-formed "HH:MM"
        values, so day/lunch bounds are parsed defensively: an unparsable day bound
        yields 0 capacity, an unparsable lunch bound is treated as "no lunch break"
        rather than crashing the whole Planning page.
        """
        day_start = self.parse_time_to_minutes(settings.day_start_time)
        day_end = self.parse_time_to_minutes(settings.day_end_time)
        if day_start is None or day_end is None:
            return 0.0
        day_minutes = day_end - day_start

        lunch_start = self.parse_time_to_minutes(settings.lunch_start_time)
        lunch_end = self.parse_time_to_minutes(settings.lunch_end_time)
        lunch_minutes = (
            lunch_end - lunch_start if lunch_start is not None and lunch_end is not None else 0
        )

        return max(day_minutes - lunch_minutes, 0) / 60

    @staticmethod
    def parse_time_to_minutes(hh_mm: str) -> int | None:
        """Parse a "HH:MM" string into a number of minutes since midnight, or None
        if the value is empty or not a well-formed "HH:MM" string."""
        if not hh_mm or ":" not in hh_mm:
            return None
        hours_str, _, minutes_str = hh_mm.partition(":")
        try:
            return int(hours_str) * 60 + int(minutes_str)
        except ValueError:
            return None

    def _format_user(self, user: User) -> str:
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name or user.email
