from datetime import date, datetime, timedelta

import reflex as rx
from gws_core import BaseModelDTO
from gws_core.space.space_service import SpaceService
from gws_project.core.working_hours_service import WorkingHoursService
from gws_project.core.working_hours_settings_dto import WorkingHoursSettingsDTO
from gws_project.planning.planning_slot_dto import (
    CreatePlanningSlotDTO,
    SlotOverlapDTO,
    UpdatePlanningSlotDTO,
)
from gws_project.planning.planning_slot_service import (
    DEFAULT_SLOT_DURATION_MINUTES,
    PlanningSlotService,
)
from gws_project.task.task_dto import TaskStatus
from gws_project.task.task_search_builder import TaskSearchBuilder
from gws_project.user.user import User
from gws_reflex_main import I18nState, ReflexMainState, toast_tr

from ..common.date_format import (
    format_date_range,
    format_day_month,
    format_short_weekday_day,
    format_short_weekday_day_month,
)
from ..common.planning_grid.planning_grid import (
    GridPersonDTO,
    GridSlotDTO,
    GridTaskDTO,
    PlanningGridDataDTO,
)


class PlanningWarningGroupDTO(BaseModelDTO):
    """One category of planning warning (overload, overlap, overdue), with its
    entries already formatted for display in the warnings dialog.

    The entries field is named `lines` and not `items`/`entries`: those are methods
    of Reflex's ObjectVar, so a field of that name is shadowed in `rx.foreach`.
    """

    title: str
    lines: list[str]


class PlanningState(rx.State):
    """State for the Planning page: a person x day weekly scheduling grid.

    Planning is indicative, never blocking: overload and overlap are computed and
    surfaced through the warnings dialog, but never prevent a slot from being
    created, moved, or resized.
    """

    # Real value is set by on_load (current week); this default only avoids a None
    # crashing computed vars (week_label, grid_data, ...) before the page has loaded.
    week_start: date = date.today()
    slots: list[GridSlotDTO] = []
    tasks: list[GridTaskDTO] = []
    people: list[GridPersonDTO] = []
    overlaps: list[SlotOverlapDTO] = []
    working_hours: WorkingHoursSettingsDTO | None = None
    warnings_dialog_open: bool = False

    # "Add a task" dialog: opened by clicking an empty area of a day column, it
    # schedules a task on that person/day/time without a drag and drop.
    add_task_dialog_open: bool = False
    add_task_target_label: str = ""  # "Alice Dupont - Mon 06 - 09:00", for the dialog
    add_task_query: str = ""
    _pending_person_id: str = ""
    _pending_day: str = ""
    _pending_start_time: str = ""

    # "Duplicate previous week" confirmation dialog: lets the user pick which
    # people's slots to duplicate before anything is written (none pre-selected).
    duplicate_dialog_open: bool = False
    duplicate_candidates: list[tuple[str, str]] = []  # (user_id, name), previous week only
    duplicate_selected_user_ids: list[str] = []

    def _monday_of(self, day: date) -> date:
        return day - timedelta(days=day.weekday())

    def _is_past_week(self) -> bool:
        """Whether the displayed week is over.

        Done tasks are still listed for such a week (its history stays readable),
        while the current and future weeks only list what is left to plan.

        :return: True when the displayed week ended before the current one
        :rtype: bool
        """
        return self.week_start < self._monday_of(date.today())

    def _due_status(self, due_date: date | None) -> str | None:
        """Urgency of a task's due date, relative to the real current date (not
        necessarily the week currently displayed in the grid)."""
        if due_date is None:
            return None
        today = date.today()
        if due_date < today:
            return "overdue"
        current_week_start = self._monday_of(today)
        current_week_end = current_week_start + timedelta(days=6)
        if current_week_start <= due_date <= current_week_end:
            return "this_week"
        return None

    async def _load_week(self):
        """Reload slots, people loads, overlaps, and the task panel for the current
        week.

        Called on load, on week navigation, and after every slot
        create/move/resize/delete.
        """
        main_state = await self.get_state(ReflexMainState)
        i18n = await self.get_state(I18nState)
        with await main_state.authenticate_user():
            settings = WorkingHoursService.get_settings()
            self.working_hours = settings.to_dto()

            people = User.get_real_users()

            slot_service = PlanningSlotService()
            slots = slot_service.get_slots_for_week(self.week_start)

            loads = slot_service.compute_week_loads(slots, people, settings)
            self.overlaps = slot_service.compute_overlaps(slots)
            overlapping_slot_ids = {o.slot_a_id for o in self.overlaps} | {o.slot_b_id for o in self.overlaps}

            self.people = [
                GridPersonDTO(
                    id=load.user.id,
                    name=f"{load.user.first_name} {load.user.last_name}".strip(),
                    photo_url=SpaceService.get_user_profile_picture_url(load.user.photo)
                    if load.user.photo
                    else None,
                    total_hours=load.total_hours,
                    capacity_hours=load.capacity_hours,
                    is_overloaded=load.is_overloaded,
                    daily_hours=load.daily_hours,
                    daily_capacity_hours=load.daily_capacity_hours,
                    overloaded_dates=load.overloaded_dates,
                )
                for load in loads
            ]

            self.slots = [
                GridSlotDTO(
                    id=slot.id,
                    task_id=slot.task.id,
                    task_title=slot.task.title,
                    project_title=slot.task.project.title,
                    company_name=slot.task.project.company.name if slot.task.project.company else None,
                    assigned_user_id=slot.assigned_user.id,
                    start_datetime=slot.start_datetime.isoformat(),
                    end_datetime=slot.end_datetime.isoformat(),
                    is_overlapping=slot.id in overlapping_slot_ids,
                )
                for slot in slots
            ]

            scheduled_task_ids = {slot.task.id for slot in slots}

            task_search = TaskSearchBuilder()
            task_search.add_allow_subtasks_filter(False)
            # Backlog is never actionable work to schedule, so it's excluded for every
            # week. Done tasks are excluded too for the current/future weeks (nothing
            # left to plan), but kept for past weeks (so history stays visible there).
            task_search.add_exclude_status_filter(TaskStatus.BACKLOG)
            if not self._is_past_week():
                task_search.add_exclude_status_filter(TaskStatus.DONE)
            tasks = task_search.search_all()

            self.tasks = [
                GridTaskDTO(
                    id=task.id,
                    title=task.title,
                    project_title=task.project.title,
                    company_name=task.project.company.name if task.project.company else None,
                    assignee_name=f"{task.assign_to.first_name} {task.assign_to.last_name}".strip(),
                    is_scheduled=task.id in scheduled_task_ids,
                    due_date_text=(
                        f"{i18n.tr('planning.due_prefix')} "
                        f"{format_day_month(task.due_date, i18n.lang)}"
                        if task.due_date
                        else None
                    ),
                    due_status=self._due_status(task.due_date),
                )
                for task in tasks
            ]

    async def on_load(self):
        """Event handler called when the page loads: default to the current week."""
        self.week_start = self._monday_of(date.today())
        await self._load_week()

    async def go_to_previous_week(self):
        self.week_start = self.week_start - timedelta(days=7)
        await self._load_week()

    async def go_to_next_week(self):
        self.week_start = self.week_start + timedelta(days=7)
        await self._load_week()

    async def go_to_current_week(self):
        self.week_start = self._monday_of(date.today())
        await self._load_week()

    @rx.var
    async def week_label(self) -> str:
        lang = (await self.get_state(I18nState)).lang
        week_end = self.week_start + timedelta(days=6)
        return format_date_range(self.week_start, week_end, lang)

    def _working_day_indices(self) -> list[int]:
        working_days = self.working_hours.working_days if self.working_hours else [0, 1, 2, 3, 4]
        return [i for i in range(7) if i in working_days]

    @rx.var
    def days(self) -> list[str]:
        return [(self.week_start + timedelta(days=i)).isoformat() for i in self._working_day_indices()]

    def _day_labels(self, lang: str) -> list[str]:
        """The column headers of the grid, e.g. "Mon 06", in the active language.

        A plain method rather than a computed var: its only consumer is `grid_data`,
        which already holds the language, and a var would have to be awaited there.

        :param lang: The active language code
        :type lang: str
        :return: One label per working day of the displayed week
        :rtype: list[str]
        """
        return [
            format_short_weekday_day(self.week_start + timedelta(days=i), lang)
            for i in self._working_day_indices()
        ]

    def _safe_time_str(self, value: str | None, default: str) -> str:
        """Admin's working-hours form does not enforce non-empty/well-formed "HH:MM"
        values, so any consumer of WorkingHoursSettings must tolerate a blank or
        malformed value rather than crash on it."""
        if value and PlanningSlotService.parse_time_to_minutes(value) is not None:
            return value
        return default

    @rx.var
    async def grid_data(self) -> PlanningGridDataDTO:
        i18n = await self.get_state(I18nState)
        settings = self.working_hours
        day_start_time = self._safe_time_str(settings.day_start_time if settings else None, "09:00")
        day_end_time = self._safe_time_str(settings.day_end_time if settings else None, "18:00")

        lunch_start_time = settings.lunch_start_time if settings else None
        lunch_end_time = settings.lunch_end_time if settings else None
        if (
            PlanningSlotService.parse_time_to_minutes(lunch_start_time or "") is None
            or PlanningSlotService.parse_time_to_minutes(lunch_end_time or "") is None
        ):
            # Incomplete/invalid lunch config in Admin: render as "no lunch break"
            # (a zero-length window) rather than crashing or fabricating a fake one.
            lunch_start_time = day_start_time
            lunch_end_time = day_start_time

        return PlanningGridDataDTO(
            days=self.days,
            day_labels=self._day_labels(i18n.lang),
            people=self.people,
            slots=self.slots,
            day_start_time=day_start_time,
            day_end_time=day_end_time,
            lunch_start_time=lunch_start_time,
            lunch_end_time=lunch_end_time,
            step_minutes=30,
            lunch_label=i18n.tr("planning.grid.lunch"),
            scheduled_label=i18n.tr("planning.grid.scheduled"),
            search_placeholder=i18n.tr("planning.tasks.search_placeholder"),
            no_task_found_label=i18n.tr("planning.tasks.no_result"),
            tasks_help_text=i18n.tr(
                "planning.tasks.help_past_week" if self._is_past_week() else "planning.tasks.help"
            ),
        )

    @rx.var
    def overdue_unscheduled_tasks(self) -> list[GridTaskDTO]:
        """Tasks whose due date has already passed and that have no slot in the
        currently viewed week (visible in the left-hand task panel, so scrolling
        there shows exactly which ones)."""
        return [task for task in self.tasks if task.due_status == "overdue" and not task.is_scheduled]

    def _build_warning_groups(self, i18n: I18nState) -> list[PlanningWarningGroupDTO]:
        """Build the warning list shown in the warnings dialog, one group per
        category, empty groups omitted.

        A plain method rather than a computed var so both `warning_groups` and
        `warning_count` can use it without one awaiting the other.

        :param i18n: the shared i18n state, for the group titles and date formats
        :type i18n: I18nState
        :return: the non-empty warning groups
        :rtype: list[PlanningWarningGroupDTO]
        """
        groups: list[PlanningWarningGroupDTO] = []

        overloaded = [
            f"{person.name} : {person.total_hours}h / {person.capacity_hours}h"
            for person in self.people
            if person.is_overloaded
        ]
        if overloaded:
            groups.append(
                PlanningWarningGroupDTO(title=i18n.tr("planning.warnings.overload"), lines=overloaded)
            )

        # One entry per (person, day): several overlapping pairs on the same day
        # are the same problem to fix, so they must not be listed twice.
        seen: set[tuple[str, str]] = set()
        overlapping: list[str] = []
        for overlap in self.overlaps:
            key = (overlap.user_id, overlap.day)
            if key in seen:
                continue
            seen.add(key)
            day_label = format_short_weekday_day_month(date.fromisoformat(overlap.day), i18n.lang)
            overlapping.append(f"{overlap.user_name} : {day_label}")
        if overlapping:
            groups.append(
                PlanningWarningGroupDTO(title=i18n.tr("planning.warnings.overlap"), lines=overlapping)
            )

        overdue = [
            f"{task.title} : {task.due_date_text}" for task in self.overdue_unscheduled_tasks
        ]
        if overdue:
            groups.append(
                PlanningWarningGroupDTO(title=i18n.tr("planning.warnings.overdue"), lines=overdue)
            )

        return groups

    @rx.var
    async def warning_groups(self) -> list[PlanningWarningGroupDTO]:
        return self._build_warning_groups(await self.get_state(I18nState))

    @rx.var
    async def warning_count(self) -> int:
        groups = self._build_warning_groups(await self.get_state(I18nState))
        return sum(len(group.lines) for group in groups)

    def open_warnings_dialog(self):
        self.warnings_dialog_open = True

    def set_warnings_dialog_open(self, value: bool):
        self.warnings_dialog_open = value

    async def _create_slot(
        self,
        main_state: ReflexMainState,
        task_id: str,
        person_id: str,
        day_str: str,
        start_time_str: str | None,
    ):
        """Schedule a task for one person, one day, one time, and reload the week.

        Shared by the two ways of adding a slot: dropping a task on a cell, and
        picking one in the "add a task" dialog. Called from a background event,
        outside the state lock (it takes it again only to reload).

        :param main_state: the shared main state, for authentication
        :type main_state: ReflexMainState
        :param task_id: the task to schedule
        :type task_id: str
        :param person_id: the user the slot is assigned to
        :type person_id: str
        :param day_str: the day of the slot, ISO formatted
        :type day_str: str
        :param start_time_str: "HH:MM" start time; the start of the working day when
            missing or malformed
        :type start_time_str: str | None
        """
        day = date.fromisoformat(day_str)

        with await main_state.authenticate_user():
            settings = WorkingHoursService.get_settings()
            day_start_str = self._safe_time_str(settings.day_start_time, "09:00")
            start_str = self._safe_time_str(start_time_str, day_start_str)
            start_time = datetime.strptime(start_str, "%H:%M").time()
            start_dt = datetime.combine(day, start_time)
            end_dt = start_dt + timedelta(minutes=DEFAULT_SLOT_DURATION_MINUTES)

            PlanningSlotService().create_slot(
                CreatePlanningSlotDTO(
                    task_id=task_id,
                    assigned_user_id=person_id,
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                )
            )

            async with self:
                await self._load_week()

    @rx.event(background=True)
    async def handle_slot_create(self, event_dict: dict):
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        try:
            task_id = event_dict.get("task_id")
            person_id = event_dict.get("person_id")
            day_str = event_dict.get("day")
            # start_time reflects where the task was actually dropped in the column.
            start_time_str = event_dict.get("start_time")
            if not task_id or not person_id or not day_str:
                yield await toast_tr.error(self, "planning.toast.invalid_drop")
                return

            await self._create_slot(main_state, task_id, person_id, day_str, start_time_str)
        except Exception as e:
            yield await toast_tr.error(
                self, "planning.toast.create_failed", {"error": str(e)}
            )

    async def handle_cell_click(self, event_dict: dict):
        """Open the "add a task" dialog on the clicked person/day/time.

        The alternative to drag and drop: the slot is only written once a task is
        picked in the dialog.
        """
        person_id = event_dict.get("person_id")
        day_str = event_dict.get("day")
        start_time_str = event_dict.get("start_time")
        if not person_id or not day_str:
            return

        i18n = await self.get_state(I18nState)
        person_name = next((p.name for p in self.people if p.id == person_id), "")
        day_label = format_short_weekday_day_month(date.fromisoformat(day_str), i18n.lang)

        self._pending_person_id = person_id
        self._pending_day = day_str
        self._pending_start_time = start_time_str or ""
        self.add_task_target_label = " - ".join(
            part for part in (person_name, day_label, start_time_str) if part
        )
        self.add_task_query = ""
        self.add_task_dialog_open = True

    def set_add_task_dialog_open(self, value: bool):
        self.add_task_dialog_open = value

    def set_add_task_query(self, value: str):
        self.add_task_query = value

    @rx.var
    def add_task_options(self) -> list[GridTaskDTO]:
        """The tasks offered by the "add a task" dialog, narrowed by its search box.

        Searches the same texts as the task panel (title, project, company, person,
        due date), so both boxes behave alike.
        """
        query = self.add_task_query.strip().lower()
        if not query:
            return self.tasks
        return [
            task
            for task in self.tasks
            if any(
                query in field.lower()
                for field in (
                    task.title,
                    task.project_title,
                    task.company_name,
                    task.assignee_name,
                    task.due_date_text,
                )
                if field
            )
        ]

    @rx.event(background=True)
    async def confirm_add_task(self, task_id: str):
        """Schedule the picked task on the cell the dialog was opened from."""
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            person_id = self._pending_person_id
            day_str = self._pending_day
            start_time_str = self._pending_start_time
            self.add_task_dialog_open = False

        if not task_id or not person_id or not day_str:
            yield await toast_tr.error(self, "planning.toast.invalid_drop")
            return

        try:
            await self._create_slot(main_state, task_id, person_id, day_str, start_time_str)
        except Exception as e:
            yield await toast_tr.error(
                self, "planning.toast.create_failed", {"error": str(e)}
            )

    @rx.event(background=True)
    async def handle_slot_move(self, event_dict: dict):
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        try:
            slot_id = event_dict.get("slot_id")
            person_id = event_dict.get("person_id")
            day_str = event_dict.get("day")
            start_time_str = event_dict.get("start_time")
            if not slot_id or not person_id or not day_str or not start_time_str:
                yield await toast_tr.error(self, "planning.toast.invalid_move")
                return

            day = date.fromisoformat(day_str)
            start_time = datetime.strptime(start_time_str, "%H:%M").time()

            with await main_state.authenticate_user():
                slot_service = PlanningSlotService()
                existing = slot_service.get_slot(slot_id)
                # Normalized to naive: the rest of this state builds naive
                # datetimes (datetime.combine has no tzinfo), and a freshly-fetched
                # slot comes back timezone-aware (DateTimeUTC.python_value) - mixing
                # the two would fail comparisons in the service.
                duration = existing.end_datetime.replace(tzinfo=None) - existing.start_datetime.replace(
                    tzinfo=None
                )

                start_dt = datetime.combine(day, start_time)
                end_dt = start_dt + duration

                slot_service.update_slot(
                    slot_id,
                    UpdatePlanningSlotDTO(
                        assigned_user_id=person_id,
                        start_datetime=start_dt,
                        end_datetime=end_dt,
                    ),
                )

                async with self:
                    await self._load_week()
        except Exception as e:
            yield await toast_tr.error(
                self, "planning.toast.move_failed", {"error": str(e)}
            )

    @rx.event(background=True)
    async def handle_slot_resize(self, event_dict: dict):
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        try:
            slot_id = event_dict.get("slot_id")
            edge = event_dict.get("edge")
            new_time_str = event_dict.get("new_time")
            if not slot_id or edge not in ("start", "end") or not new_time_str:
                yield await toast_tr.error(self, "planning.toast.invalid_resize")
                return

            new_time = datetime.strptime(new_time_str, "%H:%M").time()

            with await main_state.authenticate_user():
                slot_service = PlanningSlotService()
                existing = slot_service.get_slot(slot_id)

                start_dt = existing.start_datetime.replace(tzinfo=None)
                end_dt = existing.end_datetime.replace(tzinfo=None)
                day = start_dt.date()

                if edge == "start":
                    start_dt = datetime.combine(day, new_time)
                else:
                    end_dt = datetime.combine(day, new_time)

                slot_service.update_slot(
                    slot_id,
                    UpdatePlanningSlotDTO(
                        assigned_user_id=existing.assigned_user.id,
                        start_datetime=start_dt,
                        end_datetime=end_dt,
                    ),
                )

                async with self:
                    await self._load_week()
        except Exception as e:
            yield await toast_tr.error(
                self, "planning.toast.resize_failed", {"error": str(e)}
            )

    @rx.event(background=True)
    async def handle_slot_delete(self, slot_id: str):
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        try:
            with await main_state.authenticate_user():
                PlanningSlotService().delete_slot(slot_id)

                async with self:
                    await self._load_week()
        except Exception as e:
            yield await toast_tr.error(
                self, "planning.toast.delete_failed", {"error": str(e)}
            )

    @rx.event(background=True)
    async def open_duplicate_dialog(self):
        """Load the previous week's distinct people and open the "duplicate
        previous week" confirmation dialog, so the user can pick who to include
        before anything is written."""
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            source_week = self.week_start - timedelta(days=7)

        try:
            with await main_state.authenticate_user():
                slots = PlanningSlotService().get_slots_for_week(source_week)
                names_by_id: dict[str, str] = {}
                for slot in slots:
                    user = slot.assigned_user
                    names_by_id[user.id] = f"{user.first_name} {user.last_name}".strip()

            async with self:
                self.duplicate_candidates = sorted(names_by_id.items(), key=lambda item: item[1])
                # Nothing checked by default: duplicating a week writes slots, so the
                # user picks who is concerned rather than un-picking everyone else.
                self.duplicate_selected_user_ids = []
                self.duplicate_dialog_open = True
        except Exception as e:
            yield await toast_tr.error(
                self, "planning.toast.load_previous_week_failed", {"error": str(e)}
            )

    def set_duplicate_dialog_open(self, value: bool):
        self.duplicate_dialog_open = value

    def toggle_duplicate_person(self, user_id: str, checked: bool):
        if checked and user_id not in self.duplicate_selected_user_ids:
            self.duplicate_selected_user_ids = [*self.duplicate_selected_user_ids, user_id]
        elif not checked and user_id in self.duplicate_selected_user_ids:
            self.duplicate_selected_user_ids = [
                selected for selected in self.duplicate_selected_user_ids if selected != user_id
            ]

    @rx.event(background=True)
    async def confirm_duplicate_week(self):
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            source_week = self.week_start - timedelta(days=7)
            target_week = self.week_start
            selected_ids = list(self.duplicate_selected_user_ids)
            self.duplicate_dialog_open = False

        if not selected_ids:
            yield await toast_tr.error(self, "planning.toast.no_person_selected")
            return

        try:
            with await main_state.authenticate_user():
                duplicated = PlanningSlotService().duplicate_week(source_week, target_week, user_ids=selected_ids)

            async with self:
                await self._load_week()
                yield await toast_tr.success(
                    self, "planning.toast.duplicated", {"count": len(duplicated)}
                )
        except Exception as e:
            yield await toast_tr.error(
                self, "planning.toast.duplicate_failed", {"error": str(e)}
            )
