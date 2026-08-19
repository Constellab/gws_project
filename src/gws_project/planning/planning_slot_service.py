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

# Default length of a slot created without an explicit duration (drag & drop on the
# Planning grid, "Add to my day" on My work). The planner resizes from there.
DEFAULT_SLOT_DURATION_MINUTES = 120

# Used only when the admin working-hours settings are malformed; same values as the
# Planning grid's own fallbacks (09:00 - 18:00).
_FALLBACK_DAY_START_MINUTES = 9 * 60
_FALLBACK_DAY_END_MINUTES = 18 * 60


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

    def get_slots_for_day(self, day: date, user_id: str) -> list[PlanningSlot]:
        """Get one person's planning slots on one day, ordered by start time.

        No dedicated day filter is needed: `add_week_range_filter(day, day)` already
        bounds the query to [day 00:00, day 23:59:59].
        """
        search_builder = PlanningSlotSearchBuilder()
        search_builder.add_week_range_filter(day, day)
        search_builder.add_user_filter(user_id)

        return search_builder.search_all()

    def get_upcoming_slots_for_user(self, user_id: str, from_datetime: datetime) -> list[PlanningSlot]:
        """Get one person's slots starting at or after `from_datetime`, ordered by start time.

        The horizon is deliberately open-ended: this backs the "scheduled Thu 9:00" badge
        of the My work screen, which must show a task's next slot whenever it is, not only
        within the current week.
        """
        search_builder = PlanningSlotSearchBuilder()
        search_builder.add_user_filter(user_id)
        search_builder.add_start_from_filter(from_datetime)

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

    @ProjectDbManager.transaction()
    def reorder_day_slots(
        self,
        day: date,
        user_id: str,
        ordered_slot_ids: list[str],
        settings: WorkingHoursSettings,
    ) -> list[PlanningSlot]:
        """Re-sequence one person's slots on one day into `ordered_slot_ids`.

        The existing durations are laid back-to-back from the day's earliest start time,
        skipping the lunch break. Tasks, assignees and durations are untouched - only
        start/end move - so a reordering done from My work is immediately visible on the
        team Planning grid. The order *is* the planning, which is why My work stores no
        personal order of its own.

        Reordering compacts the day: gaps between slots disappear. That is what makes the
        operation idempotent, and the result stays freely editable from the Planning grid.

        :raises BadRequestException: if `ordered_slot_ids` is not exactly the set of the
            person's slots for that day (typically a stale frontend list).
        """
        slots = self.get_slots_for_day(day, user_id)
        slots_by_id = {slot.id: slot for slot in slots}

        if set(ordered_slot_ids) != set(slots_by_id.keys()):
            raise BadRequestException(
                "The reordered slots do not match this day's slots. Please reload the page and retry."
            )

        if not slots:
            return []

        # Keep the hour at which the day starts; only the sequence after it changes.
        cursor = min(slot.start_datetime for slot in slots)
        lunch_start, lunch_end = self._lunch_bounds(cursor, settings)

        reordered: list[PlanningSlot] = []
        for slot_id in ordered_slot_ids:
            slot = slots_by_id[slot_id]
            duration = slot.end_datetime - slot.start_datetime

            # Never lay a slot across lunch: push it past the break instead.
            if lunch_start is not None and cursor < lunch_end and cursor + duration > lunch_start:
                cursor = lunch_end

            slot.start_datetime = cursor
            slot.end_datetime = cursor + duration
            slot.save()

            cursor = slot.end_datetime
            reordered.append(slot)

        return reordered

    def find_first_free_start(
        self,
        day: date,
        duration_minutes: int,
        settings: WorkingHoursSettings,
        existing_slots: list[PlanningSlot],
    ) -> datetime | None:
        """Find the first start time on `day` where `duration_minutes` fits inside the
        working hours, given the slots already booked.

        Candidate windows are the working day, minus the lunch break, minus
        `existing_slots`. **Returns None when nothing fits** rather than proposing a time
        past the end of the day: a slot placed outside the working hours is not a warning,
        it is bad data on the team Planning - a full day has to be rearranged there.

        Takes the slots as a parameter rather than querying them, like `compute_week_loads`
        and `compute_overlaps`, so a caller that already holds the day can reuse it.

        :return: the first free start time, or None if the working day has no room left
        :rtype: datetime | None
        """
        day_start = self.parse_time_to_minutes(settings.day_start_time)
        day_end = self.parse_time_to_minutes(settings.day_end_time)
        if day_start is None or day_end is None or day_end <= day_start:
            # Admin's working-hours form does not validate "HH:MM": fall back to the same
            # 09:00-18:00 default the Planning grid uses rather than refusing to schedule.
            day_start, day_end = _FALLBACK_DAY_START_MINUTES, _FALLBACK_DAY_END_MINUTES

        windows = [(day_start, day_end)]

        lunch_start = self.parse_time_to_minutes(settings.lunch_start_time)
        lunch_end = self.parse_time_to_minutes(settings.lunch_end_time)
        if lunch_start is not None and lunch_end is not None and lunch_end > lunch_start:
            windows = self._subtract_interval(windows, lunch_start, lunch_end)

        for slot in existing_slots:
            busy_start = slot.start_datetime.hour * 60 + slot.start_datetime.minute
            windows = self._subtract_interval(
                windows, busy_start, busy_start + slot.duration_minutes()
            )

        for window_start, window_end in windows:
            if window_end - window_start >= duration_minutes:
                return self._day_minutes_to_datetime(day, window_start)

        return None

    def compute_week_loads(
        self,
        slots: list[PlanningSlot],
        people: list[User],
        settings: WorkingHoursSettings,
    ) -> list[PersonWeekLoadDTO]:
        """Compute each person's total/daily load for the given slots against the
        single, app-wide working hours settings (capacity is uniform across people)."""
        daily_capacity_hours = self.daily_capacity_hours(settings)
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

    def _lunch_bounds(
        self,
        reference: datetime,
        settings: WorkingHoursSettings,
    ) -> tuple[datetime | None, datetime | None]:
        """The lunch break as two datetimes on `reference`'s day, sharing its tzinfo.

        Built with `replace` rather than `datetime.combine` on purpose: slot datetimes are
        timezone-aware (TypedDateTimeUTC) whereas `combine` yields naive ones, and
        comparing the two raises.

        :return: (lunch start, lunch end), or (None, None) when there is no usable break.
        """
        start_minutes = self.parse_time_to_minutes(settings.lunch_start_time)
        end_minutes = self.parse_time_to_minutes(settings.lunch_end_time)
        if start_minutes is None or end_minutes is None or end_minutes <= start_minutes:
            return None, None

        midnight = reference.replace(hour=0, minute=0, second=0, microsecond=0)
        return midnight + timedelta(minutes=start_minutes), midnight + timedelta(minutes=end_minutes)

    @staticmethod
    def _subtract_interval(
        windows: list[tuple[int, int]],
        busy_start: int,
        busy_end: int,
    ) -> list[tuple[int, int]]:
        """Remove [busy_start, busy_end] from a list of ordered minute windows."""
        remaining: list[tuple[int, int]] = []
        for window_start, window_end in windows:
            if busy_end <= window_start or busy_start >= window_end:
                remaining.append((window_start, window_end))
                continue
            if window_start < busy_start:
                remaining.append((window_start, busy_start))
            if busy_end < window_end:
                remaining.append((busy_end, window_end))
        return remaining

    @staticmethod
    def _day_minutes_to_datetime(day: date, minutes: int) -> datetime:
        """Turn minutes-since-midnight into a datetime on `day`."""
        return datetime.combine(day, time.min) + timedelta(minutes=minutes)

    def _validate_time_range(self, start_datetime: datetime, end_datetime: datetime) -> None:
        if end_datetime <= start_datetime:
            raise BadRequestException("A planning slot's end time must be after its start time.")

    def daily_capacity_hours(self, settings: WorkingHoursSettings) -> float:
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
