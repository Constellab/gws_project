
from datetime import date

from gws_core import SearchBuilder

from gws_project.project.project import Project
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskStatus


class TaskSearchBuilder(SearchBuilder):

    def __init__(self) -> None:
        super().__init__(Task,  default_orders=[Task.created_at.desc()])

    def add_exclude_status_filter(self, status: TaskStatus) -> "TaskSearchBuilder":
        """Exclude tasks with a specific status from the search query
        """
        self.add_expression(Task.status != status)
        return self

    def add_projects_filter(self, project_ids: list[str]) -> "TaskSearchBuilder":
        """Filter the search query by a list of project IDs
        """
        self.add_expression(Task.project.in_(project_ids))
        return self

    def add_project_filter(self, project_id: str) -> "TaskSearchBuilder":
        """Filter the search query by a specific project ID
        """
        self.add_expression(Task.project == project_id)
        return self

    def add_company_filter(self, company_id: str) -> "TaskSearchBuilder":
        """Filter the search query by tasks whose project belongs to a specific company
        """
        self.add_join(Project, on=(Task.project == Project.id))
        self.add_expression(Project.company == company_id)
        return self

    def add_user_filter(self, user_id: str) -> "TaskSearchBuilder":
        """Filter the search query by tasks assigned to a specific user
        """
        self.add_expression(Task.assign_to == user_id)
        return self

    def add_text_search(self, search_text: str) -> "TaskSearchBuilder":
        """Filter the search query by a text search on task title and description
        """
        like_pattern = f"%{search_text}%"
        self.add_expression(Task.title.ilike(like_pattern))

        return self

    def add_allow_subtasks_filter(self, allow_subtasks: bool) -> "TaskSearchBuilder":
        """Filter the search query by whether tasks allow subtasks
        """
        self.add_expression(Task.allow_subtasks == allow_subtasks)
        return self

    def add_date_range_filter(self, start_date: date, end_date: date) -> "TaskSearchBuilder":
        """Filter the search query by tasks where dates overlap with the filter range.

        A task is included if any of these conditions are true:
        1. Task start_date falls within the filter range (start_date <= task.start_date <= end_date)
        2. Task end_date falls within the filter range (start_date <= task.end_date <= end_date)
        3. Task dates wrap/encompass the entire filter range (task.start_date <= start_date AND task.end_date >= end_date)

        Examples:
        - Filter: Jan 5-10, Task: Jan 1-7 -> Included (task end_date Jan 7 is between Jan 5-10)
        - Filter: Jan 5-10, Task: Jan 8-12 -> Included (task start_date Jan 8 is between Jan 5-10)
        - Filter: Jan 5-10, Task: Jan 1-15 -> Included (task wraps the filter range)
        - Filter: Jan 5-10, Task: Jan 11-15 -> Excluded (no overlap)

        :param start_date: The start date of the filter range
        :type start_date: date
        :param end_date: The end date of the filter range
        :type end_date: date
        """
        # Include tasks where:
        # 1. Task start_date is within filter range
        # 2. Task end_date is within filter range
        # 3. Task wraps the filter range
        self.add_expression(
            ((Task.start_date >= start_date) & (Task.start_date <= end_date)) |  # start_date in range
            ((Task.end_date >= start_date) & (Task.end_date <= end_date)) |      # end_date in range
            ((Task.start_date <= start_date) & (Task.end_date >= end_date))      # task wraps range
        )
        return self

    def add_exclude_backlog_parent_filter(self) -> "TaskSearchBuilder":
        """Exclude tasks whose parent task is in the backlog.

        Without this, the subtasks of a backlogged task surface in views that only
        exclude BACKLOG on the task itself - a subtask is not a commitment if its
        parent has not been promoted out of the backlog yet.

        The `is_null` branch is not decorative: in SQL `NULL NOT IN (...)` evaluates to
        NULL, so without it every root task (parent_task IS NULL) would be filtered out.
        """
        parent_task = Task.alias()
        backlog_parent_ids = parent_task.select(parent_task.id).where(
            parent_task.status == TaskStatus.BACKLOG
        )
        self.add_expression(
            Task.parent_task.is_null(True) | Task.parent_task.not_in(backlog_parent_ids)
        )
        return self
