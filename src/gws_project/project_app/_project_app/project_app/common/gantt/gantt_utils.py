"""Builds the portfolio Gantt payload from the project/task DTOs."""

from datetime import date, datetime

from gws_core import UserDTO
from gws_project.project.project_dto import ProjectWithRootTasksDTO
from gws_project.task.task_dto import TaskDTO, TaskStatus

from .gantt_type import GanttDataDTO, GanttProjectDTO, GanttStatus, GanttTaskDTO

# Progress at which an item counts as finished.
COMPLETE_PROGRESS = 100


def _as_date(value: date | datetime | None) -> date | None:
    """Normalise a date/datetime to a plain date.

    :param value: The value to normalise
    :type value: date | datetime | None
    :return: The corresponding date, or None
    :rtype: date | None
    """
    if isinstance(value, datetime):
        return value.date()
    return value


def resolve_status(end: date | None, progress: int, today: date) -> str:
    """Resolve the Gantt status of an item from its due date and progress.

    Finished wins over late: a project completed after its deadline is done, not late.

    :param end: Inclusive end date
    :type end: date | None
    :param progress: Completion percentage, 0-100
    :type progress: int
    :param today: The reference date
    :type today: date
    :return: One of :class:`GanttStatus`
    :rtype: str
    """
    if progress >= COMPLETE_PROGRESS:
        return GanttStatus.DONE
    if end is not None and end < today:
        return GanttStatus.LATE
    return GanttStatus.ONGOING


def get_initials(user: UserDTO | None) -> str:
    """Build the two-letter avatar initials for a user.

    :param user: The user, may be None
    :type user: UserDTO | None
    :return: Up to two uppercase letters, empty when the user is unknown
    :rtype: str
    """
    if user is None:
        return ""
    initials = f"{(user.first_name or '')[:1]}{(user.last_name or '')[:1]}".upper()
    return initials or (user.email or "")[:1].upper()


def get_full_name(user: UserDTO | None) -> str:
    """Build the display name for a user.

    :param user: The user, may be None
    :type user: UserDTO | None
    :return: The full name, falling back to the email
    :rtype: str
    """
    if user is None:
        return ""
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return name or (user.email or "")


def _build_task(task: TaskDTO, today: date) -> GanttTaskDTO:
    """Convert a root task into a Gantt row.

    A bar needs both ends, so a task missing a start or due date is returned without dates:
    it still gets a row - it counts towards the project's percentage, and leaving it out
    made that percentage impossible to reconcile with the rows - but nothing is plotted for
    it on the timeline.

    :param task: The task to convert
    :type task: TaskDTO
    :param today: The reference date
    :type today: date
    :return: The Gantt task
    :rtype: GanttTaskDTO
    """
    start = _as_date(task.start_date)
    end = _as_date(task.due_date)

    # A DONE task is finished whatever its stored progress says.
    progress = COMPLETE_PROGRESS if task.status == TaskStatus.DONE else task.progress

    if start is None or end is None:
        # No end date means nothing can be late, so such a row is only ever ongoing or done.
        return GanttTaskDTO(
            name=task.title,
            start=None,
            end=None,
            progress=progress,
            status=resolve_status(None, progress, today),
        )

    return GanttTaskDTO(
        name=task.title,
        start=start.isoformat(),
        end=end.isoformat(),
        progress=progress,
        status=resolve_status(end, progress, today),
    )


def build_gantt_data_from_projects(
    projects_with_tasks: list[ProjectWithRootTasksDTO],
    today: date | None = None,
) -> GanttDataDTO:
    """Build the Gantt payload from projects and their root tasks.

    Grouping and sorting are intentionally left to the chart: they are presentation concerns
    that change with the "show finished projects" toggle, which never round-trips.

    :param projects_with_tasks: Projects with their root tasks
    :type projects_with_tasks: list[ProjectWithRootTasksDTO]
    :param today: Reference date, defaults to the current day
    :type today: date | None
    :return: The Gantt payload
    :rtype: GanttDataDTO
    """
    reference_day = today or date.today()
    gantt_projects: list[GanttProjectDTO] = []

    for project_data in projects_with_tasks:
        project = project_data.project
        start = _as_date(project.start_date)
        end = _as_date(project.due_date)
        if start is None or end is None:
            continue

        status = resolve_status(end, project.progress, reference_day)
        late_days = (reference_day - end).days if status == GanttStatus.LATE else 0

        # Every root task gets a row, undated ones included, in the order the service
        # returned them - the same order the project's own task list uses.
        tasks = [_build_task(task, reference_day) for task in project_data.root_tasks]

        gantt_projects.append(
            GanttProjectDTO(
                id=project.id,
                name=project.title,
                start=start.isoformat(),
                end=end.isoformat(),
                progress=project.progress,
                status=status,
                owner=get_initials(project.project_manager),
                owner_name=get_full_name(project.project_manager),
                late_days=late_days,
                tasks=tasks,
            )
        )

    return GanttDataDTO(projects=gantt_projects, today=reference_day.isoformat())
