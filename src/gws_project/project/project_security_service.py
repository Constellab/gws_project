

from gws_core import (CurrentUserService, NotFoundException,
                      UnauthorizedException)
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole
from gws_project.project.project_user import ProjectUser
from gws_project.task.task import Task


class ProjectSecurityService:

    def get_and_check_role_for_project(self, project_id: str, role: ProjectUserRole) -> Project:
        """Check if the current user has read access to the project associated with the given folder ID.

        :param project_id: The ID of the project folder
        :type project_id: str
        :return: True if the user has read access, False otherwise
        :rtype: bool
        :raises NotFoundException: If no project is found for the given folder ID
        """
        current_user = CurrentUserService.get_and_check_current_user()

        # Get the project by ID
        project = Project.get_by_id(project_id)

        if not project:
            raise NotFoundException(f"No project found with ID {project_id}")

        # Check if the current user is a member of the project
        if not ProjectUser.user_has_role(project.id, current_user.id, role):
            raise UnauthorizedException(
                f"You do not have the required role '{role.name}' for this project."
            )

        return project

    def get_and_check_role_for_task(self, task_id: str, role: ProjectUserRole) -> Task:
        """Check if the current user has read access to the project associated with the given task ID.

        :param task_id: The ID of the task
        :type task_id: str
        :return: True if the user has read access, False otherwise
        :rtype: bool
        :raises NotFoundException: If no project is found for the given task ID
        """
        # Get the project by task ID
        task = Task.get_by_id(task_id)

        if not task:
            raise NotFoundException("Task not found")

        self._check_role_for_project(task.project, role)

        return task

    def _check_role_for_project(self, project: Project, role: ProjectUserRole) -> Project:
        """Check if the current user has read access to the project associated with the given folder ID.

        :param project_id: The ID of the project folder
        :type project_id: str
        :return: True if the user has read access, False otherwise
        :rtype: bool
        :raises NotFoundException: If no project is found for the given folder ID
        """
        current_user = CurrentUserService.get_and_check_current_user()

        if not project:
            raise NotFoundException(f"Project not found")

        # Check if the current user is a member of the project
        if not ProjectUser.user_has_role(project.id, current_user.id, role):
            raise UnauthorizedException(
                f"You do not have the required role '{role.name}' for this project."
            )

        return project
