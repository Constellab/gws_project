class GanttTaskDTO(BaseModelDTO):
    """DTO for a Gantt chart task.

    Attributes:
        id: Unique identifier for the task
        name: Task name
        start: Start date as ISO string
        end: End date as ISO string
        progress: Progress percentage (0-100)
        type: Task type - 'task' or 'project'
        project: ID of parent project (if this is a task)
        dependencies: List of task IDs this task depends on
        styles: Optional styles for the task bar
        display_order: Display order for sorting
        hide_children: Whether to hide children by default
    """

    id: str
    name: str
    start: str
    end: str
    progress: int
    type: str
    project: str | None = None
    dependencies: list[str] | None = None
    styles: dict | None = None
    display_order: int = 0
    hide_children: bool = False


class GanttDataDTO(BaseModelDTO):
    """DTO for the Gantt chart data structure.

    Attributes:
        tasks: List of tasks in the Gantt chart
    """

    tasks: list[GanttTaskDTO]


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
