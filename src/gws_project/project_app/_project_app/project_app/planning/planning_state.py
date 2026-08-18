from datetime import date, datetime, timedelta

import reflex as rx
from gws_core import UserDTO
from gws_core.space.space_service import SpaceService
from gws_project.company.company_dto import CompanyDTO
from gws_project.company.company_service import CompanyService
from gws_project.core.working_hours_service import WorkingHoursService
from gws_project.core.working_hours_settings_dto import WorkingHoursSettingsDTO
from gws_project.planning.planning_slot_dto import (
    CreatePlanningSlotDTO,
    SlotOverlapDTO,
    UpdatePlanningSlotDTO,
)
from gws_project.planning.planning_slot_service import PlanningSlotService
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import TaskStatus
from gws_project.task.task_search_builder import TaskSearchBuilder
from gws_project.user.user import User
from gws_reflex_main import I18nState, ReflexMainState

from ..common.planning_grid.planning_grid import (
    GridPersonDTO,
    GridSlotDTO,
    GridTaskDTO,
    PlanningGridDataDTO,
)


class PlanningState(rx.State):
    """State for the Planning page: a person x day weekly scheduling grid.

    Planning is indicative, never blocking: overload and overlap are computed and
    surfaced as dismissible banners, but never prevent a slot from being created,
    moved, or resized.
    """

    # Real value is set by on_load (current week); this default only avoids a None
    # crashing computed vars (week_label, grid_data, ...) before the page has loaded.
    week_start: date = date.today()
    slots: list[GridSlotDTO] = []
    tasks: list[GridTaskDTO] = []
    people: list[GridPersonDTO] = []
    overlaps: list[SlotOverlapDTO] = []
    working_hours: WorkingHoursSettingsDTO | None = None
    dismissed_banner_keys: set[str] = set()

    # "Duplicate previous week" confirmation dialog: lets the user pick which
    # people's slots to duplicate before anything is written.
    duplicate_dialog_open: bool = False
    duplicate_candidates: list[tuple[str, str]] = []  # (user_id, name), previous week only
    duplicate_selected_user_ids: list[str] = []

    # Filter state (project/company/person), mirroring KanbanState's convention.
    # The person filter has two different meanings depending on what it's applied
    # to: it hides all rows but that person's in the grid, while it filters the
    # task panel by that person's task.assign_to (the task's official owner).
    selected_project_id: str = ""
    selected_company_id: str = ""
    selected_user_id: str = ""
    available_projects: list[ProjectDTO] = []
    available_companies: list[CompanyDTO] = []
    available_users: list[UserDTO] = []

    async def load_projects(self):
        """Load the list of projects for the current user."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            user_projects = ProjectService().get_current_user_projects()
            self.available_projects = [project.to_dto() for project in user_projects]

    async def load_companies(self):
        """Load the list of all companies for the company filter."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            companies = CompanyService().search_companies()
            self.available_companies = [company.to_dto() for company in companies]

    async def load_users(self):
        """Load the list of all real users (excluding SYSUSER), current user first."""
        main_state = await self.get_state(ReflexMainState)
        current_user = await main_state.get_and_check_current_user()
        users = User.get_real_users()

        user_dtos = [user.to_dto() for user in users]

        current_user_dto = None
        other_users = []
        for user_dto in user_dtos:
            if user_dto.id == current_user.id:
                current_user_dto = user_dto
            else:
                other_users.append(user_dto)

        if current_user_dto:
            self.available_users = [current_user_dto] + other_users
        else:
            self.available_users = user_dtos

    def _monday_of(self, day: date) -> date:
        return day - timedelta(days=day.weekday())

    def _due_status(self, end_date: date | None) -> str | None:
        """Urgency of a task's due date, relative to the real current date (not
        necessarily the week currently displayed in the grid)."""
        if end_date is None:
            return None
        today = date.today()
        if end_date < today:
            return "overdue"
        current_week_start = self._monday_of(today)
        current_week_end = current_week_start + timedelta(days=6)
        if current_week_start <= end_date <= current_week_end:
            return "this_week"
        return None

    async def _load_week(self):
        """Reload slots, people loads, overlaps, and the task panel for the current
        week and filters.

        Does NOT touch dismissed_banner_keys: this is called after every slot
        create/move/resize/delete to refresh data, and a banner the user just
        dismissed must stay dismissed through that refresh. Only navigating to a
        different week or changing filters (see below) resets dismissals.
        """
        main_state = await self.get_state(ReflexMainState)
        i18n = await self.get_state(I18nState)
        with await main_state.authenticate_user():
            settings = WorkingHoursService.get_settings()
            self.working_hours = settings.to_dto()

            people = User.get_real_users()
            if self.selected_user_id:
                people = [person for person in people if person.id == self.selected_user_id]

            slot_service = PlanningSlotService()
            slots = slot_service.get_slots_for_week(
                self.week_start,
                project_id=self.selected_project_id or None,
                company_id=self.selected_company_id or None,
                user_id=self.selected_user_id or None,
            )

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
            if self.week_start >= self._monday_of(date.today()):
                task_search.add_exclude_status_filter(TaskStatus.DONE)
            if self.selected_project_id:
                task_search.add_project_filter(self.selected_project_id)
            if self.selected_company_id:
                task_search.add_company_filter(self.selected_company_id)
            if self.selected_user_id:
                task_search.add_user_filter(self.selected_user_id)
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
                        f"{i18n.tr('planning.due_prefix')} {task.end_date.strftime('%b %-d')}"
                        if task.end_date
                        else None
                    ),
                    due_status=self._due_status(task.end_date),
                )
                for task in tasks
            ]

    async def on_load(self):
        """Event handler called when the page loads: default to the current week."""
        self.week_start = self._monday_of(date.today())
        self.dismissed_banner_keys = set()
        await self.load_projects()
        await self.load_companies()
        await self.load_users()
        await self._load_week()

    async def go_to_previous_week(self):
        self.week_start = self.week_start - timedelta(days=7)
        self.dismissed_banner_keys = set()
        await self._load_week()

    async def go_to_next_week(self):
        self.week_start = self.week_start + timedelta(days=7)
        self.dismissed_banner_keys = set()
        await self._load_week()

    async def go_to_current_week(self):
        self.week_start = self._monday_of(date.today())
        self.dismissed_banner_keys = set()
        await self._load_week()

    async def handle_project_change(self, value: str):
        self.selected_project_id = value
        self.dismissed_banner_keys = set()
        await self._load_week()

    async def handle_company_change(self, value: str):
        self.selected_company_id = value
        self.dismissed_banner_keys = set()
        await self._load_week()

    async def handle_user_change(self, value: str):
        self.selected_user_id = value
        self.dismissed_banner_keys = set()
        await self._load_week()

    async def clear_filters(self):
        self.selected_project_id = ""
        self.selected_company_id = ""
        self.selected_user_id = ""
        self.dismissed_banner_keys = set()
        await self._load_week()

    def dismiss_banner(self, key: str):
        self.dismissed_banner_keys = self.dismissed_banner_keys | {key}

    @rx.var
    def project_options(self) -> list[tuple[str, str]]:
        return [(p.id, p.title) for p in self.available_projects]

    @rx.var
    def company_options(self) -> list[tuple[str, str]]:
        return [(c.id, c.name) for c in self.available_companies]

    @rx.var
    def week_label(self) -> str:
        week_end = self.week_start + timedelta(days=6)
        return f"{self.week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"

    def _working_day_indices(self) -> list[int]:
        working_days = self.working_hours.working_days if self.working_hours else [0, 1, 2, 3, 4]
        return [i for i in range(7) if i in working_days]

    @rx.var
    def days(self) -> list[str]:
        return [(self.week_start + timedelta(days=i)).isoformat() for i in self._working_day_indices()]

    @rx.var
    def day_labels(self) -> list[str]:
        return [
            (self.week_start + timedelta(days=i)).strftime("%a %d") for i in self._working_day_indices()
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
            day_labels=self.day_labels,
            people=self.people,
            slots=self.slots,
            day_start_time=day_start_time,
            day_end_time=day_end_time,
            lunch_start_time=lunch_start_time,
            lunch_end_time=lunch_end_time,
            step_minutes=30,
            lunch_label=i18n.tr("planning.grid.lunch"),
            scheduled_label=i18n.tr("planning.grid.scheduled"),
        )

    @rx.var
    def show_overload_banner(self) -> bool:
        return any(p.is_overloaded for p in self.people) and "overload" not in self.dismissed_banner_keys

    @rx.var
    def show_overlap_banner(self) -> bool:
        return bool(self.overlaps) and "overlap" not in self.dismissed_banner_keys

    @rx.var
    def overdue_unscheduled_tasks(self) -> list[GridTaskDTO]:
        """Tasks whose due date has already passed and that have no slot in the
        currently viewed week (visible in the left-hand task panel, so scrolling
        there shows exactly which ones)."""
        return [task for task in self.tasks if task.due_status == "overdue" and not task.is_scheduled]

    @rx.var
    def show_overdue_banner(self) -> bool:
        return bool(self.overdue_unscheduled_tasks) and "overdue" not in self.dismissed_banner_keys

    @rx.var
    async def overload_banner_text(self) -> str:
        """Names the overloaded people and their load, e.g. "Alice Dupont (42h / 35h)"."""
        i18n = await self.get_state(I18nState)
        overloaded = [p for p in self.people if p.is_overloaded]
        details = ", ".join(f"{p.name} ({p.total_hours}h / {p.capacity_hours}h)" for p in overloaded)
        return f"{i18n.tr('planning.banner.overload_prefix')} {details}"

    @rx.var
    async def overlap_banner_text(self) -> str:
        """Names each (person, day) with overlapping slots, e.g. "Alice Dupont: Mon 06"."""
        i18n = await self.get_state(I18nState)
        seen: set[tuple[str, str]] = set()
        parts: list[str] = []
        for overlap in self.overlaps:
            key = (overlap.user_id, overlap.day)
            if key in seen:
                continue
            seen.add(key)
            day_label = date.fromisoformat(overlap.day).strftime("%a %b %d")
            parts.append(f"{overlap.user_name}: {day_label}")
        return f"{i18n.tr('planning.banner.overlap_prefix')} {', '.join(parts)}"

    @rx.var
    async def overdue_banner_text(self) -> str:
        """Names each overdue, unscheduled task, e.g. "Fix bug (Due Jan 5)"."""
        i18n = await self.get_state(I18nState)
        details = ", ".join(
            f"{task.title} ({task.due_date_text})" for task in self.overdue_unscheduled_tasks
        )
        return f"{i18n.tr('planning.banner.overdue_prefix')} {details}"

    @rx.var
    def has_dismissed_banners(self) -> bool:
        return bool(self.dismissed_banner_keys)

    def reopen_banners(self):
        self.dismissed_banner_keys = set()

    @rx.event(background=True)
    async def handle_slot_create(self, event_dict: dict):
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        try:
            task_id = event_dict.get("task_id")
            person_id = event_dict.get("person_id")
            day_str = event_dict.get("day")
            start_time_str = event_dict.get("start_time")
            if not task_id or not person_id or not day_str:
                yield rx.toast.error("Invalid drop data")
                return

            day = date.fromisoformat(day_str)

            with await main_state.authenticate_user():
                settings = WorkingHoursService.get_settings()
                # start_time reflects where the task was actually dropped in the
                # column; fall back to the start of the working day if missing/invalid.
                day_start_str = self._safe_time_str(settings.day_start_time, "09:00")
                start_str = self._safe_time_str(start_time_str, day_start_str)
                start_time = datetime.strptime(start_str, "%H:%M").time()
                start_dt = datetime.combine(day, start_time)
                end_dt = start_dt + timedelta(hours=2)

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
        except Exception as e:
            yield rx.toast.error(f"Error creating slot: {e}")

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
                yield rx.toast.error("Invalid move data")
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
            yield rx.toast.error(f"Error moving slot: {e}")

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
                yield rx.toast.error("Invalid resize data")
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
            yield rx.toast.error(f"Error resizing slot: {e}")

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
            yield rx.toast.error(f"Error deleting slot: {e}")

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
                self.duplicate_selected_user_ids = list(names_by_id.keys())
                self.duplicate_dialog_open = True
        except Exception as e:
            yield rx.toast.error(f"Error loading previous week: {e}")

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
            yield rx.toast.error("Select at least one person to duplicate")
            return

        try:
            with await main_state.authenticate_user():
                duplicated = PlanningSlotService().duplicate_week(source_week, target_week, user_ids=selected_ids)

            async with self:
                await self._load_week()
                yield rx.toast.success(f"{len(duplicated)} slot(s) duplicated from last week")
        except Exception as e:
            yield rx.toast.error(f"Error duplicating previous week: {e}")
