
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

    def add_project_filter(self, project_id: str) -> "TaskSearchBuilder":
        """Filter the search query by a specific project ID
        """
        self.add_expression(Task.project == project_id)
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
        self.add_expression(
            (Task.title.ilike(like_pattern)) |
            (Task.description.ilike(like_pattern))
        )
        return self
