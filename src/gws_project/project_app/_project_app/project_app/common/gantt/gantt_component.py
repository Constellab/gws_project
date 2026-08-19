"""Reflex wrapper for the portfolio Gantt chart."""

import reflex as rx
from gws_reflex_main import translate
from reflex.vars import Var

from . import gantt_translations  # noqa: F401  (side effect: registers translations)
from .gantt_type import GanttDataDTO

# Path to the custom TSX component
gantt_path = rx.asset("gantt_chart.tsx", shared=True)
public_gantt_path = "$/public/" + gantt_path

# Labels the chart draws itself. It is a React component, so translate() cannot be called
# inside it; the resolved strings are handed down as one reactive prop.
_LABEL_KEYS = [
    "column_project",
    "column_meta",
    "group_late",
    "group_ongoing",
    "group_done",
    "project_one",
    "project_many",
    "task_one",
    "task_many",
    "late_by",
    "done",
    "empty",
]


def _to_camel(name: str) -> str:
    """Convert a snake_case label key to the camelCase the chart expects.

    :param name: The snake_case key
    :type name: str
    :return: The camelCase key
    :rtype: str
    """
    head, *rest = name.split("_")
    return head + "".join(part.capitalize() for part in rest)


class GanttChart(rx.Component):
    """Portfolio Gantt chart: projects grouped by status on a pixels-per-day timeline.

    Rows are grouped En retard / En cours / Terminé and sorted by end date. The left column
    and the two-row time axis are frozen; the chart re-centres on today whenever the zoom
    changes or ``recenter_token`` is bumped.
    """

    library = public_gantt_path
    tag = "GanttChart"

    # Projects, their root tasks and the server's idea of "today"
    data: Var[GanttDataDTO]

    # Zoom level: 'Day', 'Week', 'Month' or 'Year'
    view_mode: Var[str]

    # Whether the "Terminé" group is drawn at all
    show_completed: Var[bool]

    # Any change re-centres the timeline on today (the "Aujourd'hui" button bumps it)
    recenter_token: Var[int]

    # BCP 47 locale tag used for every date the chart renders
    locale: Var[str]

    # Translated labels, keyed camelCase
    labels: Var[dict[str, str]]

    # Fired with the project id when a project name is clicked
    on_task_click: rx.EventHandler[rx.event.passthrough_event_spec(str)]


gantt_chart = GanttChart.create


def gantt_component(
    data: GanttDataDTO,
    view_mode: str,
    show_completed: bool,
    recenter_token: int,
    on_task_click: rx.EventHandler,
) -> rx.Component:
    """Create the portfolio Gantt chart.

    :param data: Projects, tasks and today's date
    :type data: GanttDataDTO
    :param view_mode: Zoom level ('Day', 'Week', 'Month', 'Year')
    :type view_mode: str
    :param show_completed: Whether finished projects are shown
    :type show_completed: bool
    :param recenter_token: Bump to re-centre the timeline on today
    :type recenter_token: int
    :param on_task_click: Handler receiving the clicked project id
    :type on_task_click: rx.EventHandler
    :return: The Gantt chart component
    :rtype: rx.Component
    """
    return gantt_chart(
        data=data,
        view_mode=view_mode,
        show_completed=show_completed,
        recenter_token=recenter_token,
        locale=translate("gantt_chart.locale"),
        labels={_to_camel(key): translate(f"gantt_chart.{key}") for key in _LABEL_KEYS},
        on_task_click=on_task_click,
    )
