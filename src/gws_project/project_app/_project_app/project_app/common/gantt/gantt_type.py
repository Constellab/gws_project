from gws_core import BaseModelDTO


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
