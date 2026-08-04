from datetime import date

from gws_project.project.project_dto import ProjectWithRootTasksDTO
from gws_project.task.task_dto import TaskStatus

from .gantt_type import GanttDataDTO, GanttTaskDTO


def get_status_color(status: TaskStatus) -> dict:
    """Get color styles based on task status.

    :param status: Task status
    :type status: TaskStatus
    :return: Dictionary with backgroundColor and progressColor
    :rtype: dict
    """
    status_colors = {
        TaskStatus.BACKLOG: {
            "backgroundColor": "var(--accent-4)",
            "progressColor": "var(--accent-9)",
            "progressSelectedColor": "var(--accent-9)",
        },
        TaskStatus.TODO: {
            "backgroundColor": "var(--accent-4)",
            "progressColor": "var(--accent-9)",
            "progressSelectedColor": "var(--accent-9)",
        },
        TaskStatus.DOING: {
            "backgroundColor": "var(--accent-4)",
            "progressColor": "var(--accent-9)",
            "progressSelectedColor": "var(--accent-9)",
        },
        TaskStatus.DONE: {
            "backgroundColor": "var(--accent-9)",
            "progressColor": "var(--accent-9)",
            "progressSelectedColor": "var(--accent-9)",
        },
    }
    return status_colors.get(status, status_colors[TaskStatus.TODO])


def build_gantt_data_from_projects(projects_with_tasks: list[ProjectWithRootTasksDTO]) -> GanttDataDTO:
    """Build Gantt chart data from projects with their root tasks.

    This utility function converts ProjectWithRootTasksDTO objects into a Gantt chart format.
    Projects are displayed as project rows, and tasks are displayed as task rows grouped under their project.

    :param projects_with_tasks: List of projects with their root tasks
    :type projects_with_tasks: List[ProjectWithRootTasksDTO]
    :return: GanttDataDTO with tasks structure for the Gantt chart
    :rtype: GanttDataDTO
    """
    gantt_tasks = []
    display_order = 1

    for project_data in projects_with_tasks:
        project = project_data.project
        root_tasks = project_data.root_tasks

        # Add project row
        project_task = GanttTaskDTO(
            id=f"project-{project.id}",
            name=project.title,
            start=project.start_date.isoformat() if isinstance(project.start_date, date) else project.start_date,
            end=project.end_date.isoformat() if isinstance(project.end_date, date) else project.end_date,
            progress=project.progress,
            type="project",
            styles={
                "backgroundColor": "var(--accent-9)",
                "progressColor": "var(--accent-9)",
                "progressSelectedColor": "var(--accent-9)",
            },
            display_order=display_order,
        )
        gantt_tasks.append(project_task)
        display_order += 1

        # Add task rows for this project. A task needs both dates to be plotted as a
        # bar, so tasks with a missing start or end date are skipped here (they still
        # show up in the regular task list and kanban board).
        for task in root_tasks:
            if task.start_date is None or task.end_date is None:
                continue

            task_styles = get_status_color(task.status)

            task_item = GanttTaskDTO(
                id=task.id,
                name=task.title,
                start=task.start_date.isoformat() if isinstance(task.start_date, date) else task.start_date,
                end=task.end_date.isoformat() if isinstance(task.end_date, date) else task.end_date,
                progress=task.progress,
                type="task",
                project=f"project-{project.id}",
                styles=task_styles,
                display_order=display_order,
            )
            gantt_tasks.append(task_item)
            display_order += 1

    return GanttDataDTO(tasks=gantt_tasks)
