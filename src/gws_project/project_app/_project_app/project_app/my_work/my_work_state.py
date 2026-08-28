from datetime import date

import reflex as rx
from gws_core import BaseModelDTO
from gws_project.my_work.my_work_dto import MyDaySlotDTO, MyRestTaskDTO, MyWorkDTO
from gws_project.my_work.my_work_service import MyWorkService
from gws_reflex_base import ReflexAppException
from gws_reflex_main import I18nState, ReflexMainState, toast_tr

from ..common.date_format import (
    format_day_month,
    format_short_weekday_time,
    format_time,
)
from ..common.details_sidebar.details_panel_state import DetailsPanelState
from ..common.my_day_list.my_day_list import MyDayItemDTO


class MyRestItemDTO(BaseModelDTO):
    """One task row of "The rest".

    Like the slot rows, every displayed value is a string resolved server-side. Optional
    values are empty strings rather than None, so the component tests them with a plain
    comparison instead of a null check.
    """

    task_id: str
    title: str
    parent_task_title: str = ""
    project_title: str
    due_date_text: str = ""
    is_overdue: bool = False
    scheduled_label: str = ""  # e.g. "scheduled Thu 09:00", empty when not scheduled


class MyWorkState(rx.State):
    """State of the My work page: the signed-in user's day and what is waiting behind it.

    The state holds no query logic - MyWorkService derives both lists - and no user id: the
    service resolves the signed-in user itself, which is what keeps the page personal.
    """

    day_label: str = ""
    planned_label: str = ""
    # Empty unless the day goes past the working hours; indicative, never blocking.
    over_capacity_note: str = ""
    reorder_label: str = ""
    # False when the working day has no room left for another slot: "Add to my day" is then
    # disabled, because appending work outside the working hours corrupts the team Planning.
    can_add_to_day: bool = True
    add_to_day_hint: str = ""
    day_items: list[MyDayItemDTO] = []
    rest_items: list[MyRestItemDTO] = []

    @rx.var
    def rest_count(self) -> int:
        return len(self.rest_items)

    @rx.var
    def has_day_items(self) -> bool:
        return len(self.day_items) > 0

    @rx.var
    def has_rest_items(self) -> bool:
        return len(self.rest_items) > 0

    @rx.var
    def add_to_day_disabled(self) -> bool:
        return not self.can_add_to_day

    @rx.var
    def is_empty(self) -> bool:
        """Nothing scheduled and nothing assigned: the page explains how work arrives."""
        return not self.day_items and not self.rest_items

    async def on_load(self):
        """Event handler called when the page loads."""
        await self._reload()

    @rx.event
    async def handle_reorder(self, event_dict: dict):
        """Apply a new order to the day, rewriting the slots' times.

        The reordering is not stored as a preference: it moves the planning slots, so it is
        immediately visible to whoever plans the team.
        """
        ordered_slot_ids = event_dict.get("ordered_slot_ids") or []
        if not ordered_slot_ids:
            return

        main_state = await self.get_state(ReflexMainState)
        i18n = await self.get_state(I18nState)

        with await main_state.authenticate_user():
            my_work = MyWorkService().reorder_my_day(ordered_slot_ids)

        self._apply(my_work, i18n)

    @rx.event
    async def handle_add_to_my_day(self, task_id: str):
        """Ask the Planning for a slot at the first free time range of the working day."""
        if not self.can_add_to_day:
            # The button is disabled, but the page can be stale - the day may have filled up
            # from the Planning or another tab. The service refuses too; checking here only
            # makes the message translatable.
            i18n = await self.get_state(I18nState)
            raise ReflexAppException(i18n.tr("my_work.rest.day_full"))

        main_state = await self.get_state(ReflexMainState)

        with await main_state.authenticate_user():
            MyWorkService().add_to_my_day(task_id)

        await self._reload()
        yield await toast_tr.success(self, "my_work.toast.added")

    async def handle_open_task(self, task_id: str):
        """Show the clicked task in the details panel.

        The page is a short, ordered reading of the day: leaving it for the task detail
        page on every click lost that order. Both lists are reloaded after an edit, since
        a task marked done drops out of them.

        :param task_id: The id of the clicked task
        :type task_id: str
        """
        details_panel = await self.get_state(DetailsPanelState)
        await details_panel.open_task(task_id, callback_after_change=self._reload)

    async def _reload(self) -> None:
        """Reload both lists. Not an rx.event: only ever called from other handlers."""
        main_state = await self.get_state(ReflexMainState)
        i18n = await self.get_state(I18nState)

        with await main_state.authenticate_user():
            my_work = MyWorkService().get_my_work()

        self._apply(my_work, i18n)

    def _apply(self, my_work: MyWorkDTO, i18n: I18nState) -> None:
        """Turn the service's DTO into the page's pre-formatted vars."""
        # The page always reads today (the state never passes a day to the service), so the
        # heading names it as such rather than spelling out the date.
        self.day_label = i18n.tr("my_work.day.today")
        self.planned_label = self._format_planned(my_work.planned_minutes, i18n)
        self.over_capacity_note = (
            i18n.tr(
                "my_work.day.over_capacity",
                {"capacity": self._format_hours(my_work.daily_capacity_minutes)},
            )
            if my_work.is_over_capacity
            else ""
        )
        self.reorder_label = i18n.tr("my_work.reorder")
        self.can_add_to_day = my_work.can_add_to_day
        self.add_to_day_hint = i18n.tr(
            "my_work.rest.add_to_day" if my_work.can_add_to_day else "my_work.rest.day_full"
        )
        self.day_items = [self._to_day_item(slot, i18n) for slot in my_work.day_slots]
        self.rest_items = [self._to_rest_item(task, i18n) for task in my_work.rest_tasks]

    def _to_day_item(self, slot: MyDaySlotDTO, i18n: I18nState) -> MyDayItemDTO:
        # Being scheduled past the deadline is the more precise of the two warnings, so it
        # takes precedence when both apply.
        due_status = None
        if slot.is_scheduled_after_due:
            due_status = "after_due"
        elif slot.is_overdue:
            due_status = "overdue"

        return MyDayItemDTO(
            slot_id=slot.slot_id,
            task_id=slot.task_id,
            task_title=slot.task_title,
            parent_task_title=slot.parent_task_title,
            project_title=slot.project_title,
            time_range=(
                f"{format_time(slot.start_datetime)} - {format_time(slot.end_datetime)}"
            ),
            due_date_text=self._format_due(slot.due_date, i18n),
            due_status=due_status,
            assignee_note=(
                i18n.tr("my_work.other_assignee", {"name": slot.other_assignee_name})
                if slot.other_assignee_name
                else None
            ),
        )

    def _to_rest_item(self, task: MyRestTaskDTO, i18n: I18nState) -> MyRestItemDTO:
        return MyRestItemDTO(
            task_id=task.task_id,
            title=task.title,
            parent_task_title=task.parent_task_title or "",
            project_title=task.project_title,
            due_date_text=self._format_due(task.due_date, i18n) or "",
            is_overdue=task.is_overdue,
            scheduled_label=(
                i18n.tr(
                    "my_work.rest.scheduled",
                    {"when": format_short_weekday_time(task.next_slot_start, i18n.lang)},
                )
                if task.next_slot_start
                else ""
            ),
        )

    def _format_due(self, due_date: date | None, i18n: I18nState) -> str | None:
        if due_date is None:
            return None
        return (
            f"{i18n.tr('my_work.due_prefix')} {format_day_month(due_date, i18n.lang)}"
        )

    @staticmethod
    def _format_planned(minutes: int, i18n: I18nState) -> str:
        """The day's planned total, e.g. "5h 30 planned"."""
        if minutes <= 0:
            return i18n.tr("my_work.day.nothing_planned")

        hours, remaining_minutes = divmod(minutes, 60)
        if hours and remaining_minutes:
            return i18n.tr(
                "my_work.day.planned", {"hours": hours, "minutes": remaining_minutes}
            )
        if hours:
            return i18n.tr("my_work.day.planned_hours", {"hours": hours})
        return i18n.tr("my_work.day.planned_minutes", {"minutes": remaining_minutes})

    @staticmethod
    def _format_hours(minutes: int) -> str:
        hours = minutes / 60
        return f"{hours:.0f}" if hours.is_integer() else f"{hours:.1f}"
