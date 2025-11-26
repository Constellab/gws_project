"""Reflex wrapper for React Gantt chart component using gantt-task-react."""

import reflex as rx
from reflex.vars import Var

from .gantt_type import GanttDataDTO

# Path to the custom TSX component
gantt_path = rx.asset("gantt_chart.tsx", shared=True)
public_gantt_path = "$/public/" + gantt_path


class GanttChart(rx.Component):
    """Custom Gantt Chart component using gantt-task-react.

    A interactive Gantt chart that displays projects and their tasks in a timeline view.
    Tasks are grouped by project and displayed with progress bars.

    Example:
        ```python
        from project_app.common.gantt import gantt_chart

        gantt_chart(
            data={
                "tasks": [
                    {
                        "id": "project-1",
                        "name": "Project Alpha",
                        "start": "2024-01-01",
                        "end": "2024-03-31",
                        "progress": 45,
                        "type": "project"
                    },
                    {
                        "id": "task-1",
                        "name": "Task 1",
                        "start": "2024-01-01",
                        "end": "2024-01-15",
                        "progress": 100,
                        "type": "task",
                        "project": "project-1"
                    }
                ]
            },
            on_task_click=MyState.handle_task_click,
        )
        ```
    """

    # Use the custom JSX component
    library = public_gantt_path
    tag = "GanttChart"

    # Component props
    data: Var[GanttDataDTO]

    # View mode: 'Day', 'Week', 'Month', 'Year'
    view_mode: Var[str]

    # Event handler for task click
    on_task_click: rx.EventHandler[rx.event.passthrough_event_spec(str)]


# Convenience function to create the component
gantt_chart = GanttChart.create


def _empty_state() -> rx.Component:
    """Create an empty state component when no projects are available.

    :return: Empty state component
    :rtype: rx.Component
    """
    return rx.box(
        rx.vstack(
            rx.text("📊", font_size="48px"),
            rx.heading("No Projects Available", size="5", font_weight="600"),
            rx.text("Create a project with tasks to see the Gantt chart.", font_size="14px", color="gray"),
            spacing="3",
            align="center",
        ),
        text_align="center",
        background_color="var(--gray-2)",
        border_radius="8px",
        width="100%",
    )


def gantt_component(data: GanttDataDTO, view_mode: str, on_task_click: rx.EventHandler) -> rx.Component:
    """Create a Gantt chart component.

    :param data: Gantt chart data
    :type data: GanttDataDTO
    :param view_mode: View mode ('Day', 'Week', 'Month', 'Year')
    :type view_mode: str
    :param on_task_click: Event handler for task click
    :type on_task_click: rx.EventHandler
    :return: Gantt chart component
    :rtype: rx.Component
    """
    # Show empty state if no projects, otherwise show Gantt chart
    return rx.cond(
        data.tasks.length() > 0,
        gantt_chart(
            data=data,
            view_mode=view_mode,
            on_task_click=on_task_click,
        ),
        _empty_state(),
    )
