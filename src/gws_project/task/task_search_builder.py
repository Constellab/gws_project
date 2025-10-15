
from gws_core import SearchBuilder
from gws_project.task.task import Task


class TaskSearchBuilder(SearchBuilder):

    def __init__(self) -> None:
        super().__init__(Task,  default_orders=[Task.created_at.desc()])

    def add_projects_filter(self, project_ids: list[str]) -> "TaskSearchBuilder":
        """Filter the search query by a list of project IDs
        """
        self.add_expression(Task.project.in_(project_ids))
        return self
