"""DTOs for the portfolio Gantt view.

The frontend receives a ready-to-draw structure: statuses are already resolved, owners are
already reduced to initials and dates are plain ISO strings. Nothing here is meant to be
recomputed client-side beyond geometry.
"""

from gws_core import BaseModelDTO


class GanttStatus:
    """The only three statuses the Gantt knows about.

    Deliberately not a mirror of ``ProjectStatus`` / ``TaskStatus``: those describe what the
    user declared, this describes where the item stands against today's date. There is no
    "to start" or "planned" state — anything not late and not finished is ongoing.
    """

    ONGOING = "encours"
    LATE = "retard"
    DONE = "termine"


class GanttTaskDTO(BaseModelDTO):
    """A single bar on the chart.

    Attributes:
        name: Label drawn on (or next to) the bar
        start: Inclusive start date, ISO ``YYYY-MM-DD``
        end: Inclusive end date, ISO ``YYYY-MM-DD``
        progress: Completion percentage, 0-100
        status: One of :class:`GanttStatus`
    """

    name: str
    start: str
    end: str
    progress: int
    status: str


class GanttProjectDTO(GanttTaskDTO):
    """A project row, with the tasks that collapse underneath it.

    Attributes:
        id: Project id, used to route on click and to key the expanded state
        owner: Project manager initials, e.g. ``MB``
        owner_name: Full manager name, used in the bar tooltip
        late_days: Days past the end date when late, else 0
        tasks: Root tasks that have both dates set
    """

    id: str
    owner: str
    owner_name: str
    late_days: int = 0
    tasks: list[GanttTaskDTO] = []


class GanttDataDTO(BaseModelDTO):
    """Everything the chart needs for one render.

    Attributes:
        projects: Projects to draw, in no particular order (the chart groups and sorts)
        today: Today's date, ISO ``YYYY-MM-DD``, resolved server-side so the chart and the
            backend never disagree about what "late" means across timezones
    """

    projects: list[GanttProjectDTO] = []
    today: str = ""
