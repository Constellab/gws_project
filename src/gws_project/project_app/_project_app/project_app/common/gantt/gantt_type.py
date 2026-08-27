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
    """A single row of the chart, with a bar when it has a period.

    A task missing either date carries ``start``/``end`` as None: it is still listed, so
    the rows account for the whole of the project's percentage, but it draws no period and
    no bar. Projects always have both dates - one that doesn't is left out of the payload
    altogether.

    Attributes:
        id: The task's own id, which keys its expanded state in the chart
        name: Label drawn on (or next to) the bar
        start: Inclusive start date, ISO ``YYYY-MM-DD``, or None when undated
        end: Inclusive end date, ISO ``YYYY-MM-DD``, or None when undated
        progress: Completion percentage, 0-100
        status: One of :class:`GanttStatus`
    """

    id: str
    name: str
    start: str | None = None
    end: str | None = None
    progress: int
    status: str
    # Subtasks, in the project's own order. Recursive: subtasks nest without a depth limit,
    # and each level collapses under its own row.
    tasks: list["GanttTaskDTO"] = []


# The self-reference above is a forward declaration, so the model has to be rebuilt once the
# class exists for pydantic to resolve it.
GanttTaskDTO.model_rebuild()


class GanttProjectDTO(GanttTaskDTO):
    """A project row, with the root tasks that collapse underneath it.

    Attributes:
        owner: Project manager initials, e.g. ``MB``
        owner_name: Full manager name, used in the bar tooltip
        late_days: Days past the due date when late, else 0
    """

    owner: str
    owner_name: str
    late_days: int = 0


class GanttDataDTO(BaseModelDTO):
    """Everything the chart needs for one render.

    Attributes:
        projects: Projects to draw, in no particular order (the chart groups and sorts)
        today: Today's date, ISO ``YYYY-MM-DD``, resolved server-side so the chart and the
            backend never disagree about what "late" means across timezones
    """

    projects: list[GanttProjectDTO] = []
    today: str = ""
