from datetime import date

from gws_core import SearchBuilder

from gws_project.project.project import Project
from gws_project.project.project_user import ProjectUser


class ProjectSearchBuilder(SearchBuilder):
    def __init__(self) -> None:
        super().__init__(Project, default_orders=[Project.title])

    def add_project_manager_filter(self, user_id: str) -> "ProjectSearchBuilder":
        """Filter the search query by projects managed by a specific user"""
        self.add_expression(Project.project_manager == user_id)
        return self

    def add_text_search(self, search_text: str) -> "ProjectSearchBuilder":
        """Filter the search query by a text search on project title and description"""
        like_pattern = f"%{search_text}%"
        self.add_expression(Project.title.ilike(like_pattern))

        return self

    def add_company_filter(self, company_id: str) -> "ProjectSearchBuilder":
        """Filter the search query by projects belonging to a specific company"""
        self.add_expression(Project.company == company_id)
        return self

    def add_project_user_filter(self, user_id: str) -> "ProjectSearchBuilder":
        """Filter the search query by projects where a user is a member (via ProjectUser table)

        :param user_id: The user ID to filter by
        :type user_id: str
        :return: The search builder instance for chaining
        :rtype: ProjectSearchBuilder
        """
        self.add_join(ProjectUser, on=((ProjectUser.project == Project.id) & (ProjectUser.user == user_id)))
        return self

    def add_date_range_filter(self, start_date: date, end_date: date) -> "ProjectSearchBuilder":
        """Filter the search query by projects where dates overlap with the filter range.

        A project is included if any of these conditions are true:
        1. Project start_date falls within the filter range (start_date <= project.start_date <= end_date)
        2. Project due_date falls within the filter range (start_date <= project.due_date <= end_date)
        3. Project dates wrap/encompass the entire filter range (project.start_date <= start_date AND project.due_date >= end_date)

        Examples:
        - Filter: Jan 5-10, Project: Jan 1-7 -> Included (project due_date Jan 7 is between Jan 5-10)
        - Filter: Jan 5-10, Project: Jan 8-12 -> Included (project start_date Jan 8 is between Jan 5-10)
        - Filter: Jan 5-10, Project: Jan 1-15 -> Included (project wraps the filter range)
        - Filter: Jan 5-10, Project: Jan 11-15 -> Excluded (no overlap)

        :param start_date: The start date of the filter range
        :type start_date: date
        :param end_date: The end date of the filter range
        :type end_date: date
        """
        # Include projects where:
        # 1. Project start_date is within filter range
        # 2. Project due_date is within filter range
        # 3. Project wraps the filter range
        self.add_expression(
            ((Project.start_date >= start_date) & (Project.start_date <= end_date))  # start_date in range
            | ((Project.due_date >= start_date) & (Project.due_date <= end_date))  # due_date in range
            | ((Project.start_date <= start_date) & (Project.due_date >= end_date))  # project wraps range
        )
        return self
