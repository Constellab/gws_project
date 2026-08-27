"""Reflex wrapper for the custom React Planning grid component (person x day)."""

import reflex as rx
from gws_core import BaseModelDTO
from reflex.vars import Var

# Path to the custom TSX components
planning_grid_path = rx.asset("planning_grid.tsx", shared=True)
rx.asset("planning_grid_types.ts", shared=True)
rx.asset("planning_grid_utils.ts", shared=True)
rx.asset("task_panel.tsx", shared=True)
rx.asset("day_cell.tsx", shared=True)
rx.asset("planning_slot_block.tsx", shared=True)
public_planning_grid_path = "$/public/" + planning_grid_path


class GridPersonDTO(BaseModelDTO):
    """A person row of the Planning grid, with their computed weekly load."""

    id: str
    name: str
    photo_url: str | None = None
    total_hours: float
    capacity_hours: float
    is_overloaded: bool
    daily_hours: dict[str, float]  # ISO date -> hours
    daily_capacity_hours: float
    overloaded_dates: list[str]


class GridSlotDTO(BaseModelDTO):
    """One planning slot (créneau) rendered in the grid."""

    id: str
    task_id: str
    task_title: str
    project_title: str
    company_name: str | None = None
    assigned_user_id: str
    start_datetime: str  # ISO datetime
    end_datetime: str  # ISO datetime
    is_overlapping: bool = False


class GridTaskDTO(BaseModelDTO):
    """One task row of the left-hand task panel."""

    id: str
    title: str
    project_title: str
    company_name: str | None = None
    assignee_name: str
    is_scheduled: bool = False
    due_date_text: str | None = None  # pre-formatted, e.g. "Due May 9"
    due_status: str | None = None  # "overdue" | "this_week" | None


class PlanningGridDataDTO(BaseModelDTO):
    """Everything the Planning grid needs to render one week.

    `days`/`day_labels` only ever list working days (per WorkingHoursSettings) -
    non-working days are filtered out server-side, so the grid never renders them.
    """

    days: list[str]  # ISO dates, working days only
    day_labels: list[str]  # pre-formatted, e.g. "Mon 6"
    people: list[GridPersonDTO]
    slots: list[GridSlotDTO]
    day_start_time: str  # "HH:MM"
    day_end_time: str  # "HH:MM"
    lunch_start_time: str  # "HH:MM"
    lunch_end_time: str  # "HH:MM"
    step_minutes: int = 30
    # Resolved server-side (via I18nState) so the custom TSX component - which has no
    # access to the Python translation system - still reacts to a language switch.
    lunch_label: str = "Lunch"
    scheduled_label: str = "Scheduled"
    search_placeholder: str = "Search"
    no_task_found_label: str = "No task found"
    # Caption under the task list, telling which tasks it lists.
    tasks_help_text: str = ""


class PlanningGrid(rx.Component):
    """Custom person x day scheduling grid, built with @dnd-kit.

    Supports dragging a task from the left panel onto a cell (create), dragging an
    existing slot to another person/day (move, duration preserved), and resizing a
    slot's edges with dedicated pointer-driven handles (kept outside of dnd-kit's
    DndContext, which has no resize primitive).
    """

    library = public_planning_grid_path
    tag = "PlanningGrid"

    grid_data: Var[PlanningGridDataDTO]
    tasks: Var[list[GridTaskDTO]]

    # Fired when a task from the left panel is dropped onto a cell: {task_id, person_id, day, start_time}
    on_slot_create: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    # Fired when an existing slot is dropped onto another cell: {slot_id, person_id, day, start_time}
    on_slot_move: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    # Fired when a slot's edge is resized: {slot_id, edge, new_time}
    on_slot_resize: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    # Fired when a slot's delete button is clicked, with the slot id
    on_slot_delete: rx.EventHandler[rx.event.passthrough_event_spec(str)]


planning_grid = PlanningGrid.create
