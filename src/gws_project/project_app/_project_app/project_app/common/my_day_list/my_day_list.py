"""Reflex wrapper for the custom React drag-to-reorder list of "My day"."""

import reflex as rx
from gws_core import BaseModelDTO
from reflex.vars import Var

# Path to the custom TSX components. Every file must be a shared asset, otherwise the
# relative TS imports between them do not resolve at build time.
my_day_list_path = rx.asset("my_day_list.tsx", shared=True)
rx.asset("my_day_list_types.ts", shared=True)
rx.asset("my_day_item.tsx", shared=True)
public_my_day_list_path = "$/public/" + my_day_list_path


class MyDayItemDTO(BaseModelDTO):
    """One slot row of "My day".

    Everything displayed is a string resolved server-side, including the translated ones:
    the custom TSX component has no access to the Python i18n system, yet the rows must
    still follow a language switch.
    """

    slot_id: str
    task_id: str
    task_title: str
    parent_task_title: str | None = None
    project_title: str
    time_range: str  # pre-formatted, e.g. "09:00 - 11:00"
    due_date_text: str | None = None  # pre-formatted, e.g. "Due Mar 4"
    due_status: str | None = None  # "overdue" | "after_due" | None
    assignee_note: str | None = None  # set only when the task belongs to someone else


class MyDayList(rx.Component):
    """Vertical, drag-to-reorder list of the signed-in user's slots for the day.

    Reordering is not a display preference: the emitted order is applied to the planning
    slots' times, so the list only ever proposes an order and the server decides the
    resulting schedule.
    """

    library = public_my_day_list_path
    tag = "MyDayList"

    items: Var[list[MyDayItemDTO]]
    reorder_label: Var[str]

    # Fired after a drag, with the slot ids in their new order: {ordered_slot_ids: [...]}
    on_reorder: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    # Fired when a row is clicked, with the id of its task
    on_item_click: rx.EventHandler[rx.event.passthrough_event_spec(str)]


my_day_list = MyDayList.create
