from datetime import datetime
from enum import Enum

from gws_core import BaseModelDTO, ModelDTO, RichTextDTO, UserDTO

from gws_project.task.task_dto import TaskDTO


class ProjectStatus(Enum):
    """Status of a project"""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class ProjectUserRole(Enum):
    """Role of a user in a project"""

    OWNER = "OWNER"
    USER = "USER"

    def get_access_level(self) -> int:
        """Get the access level corresponding to the role.

        :return: Access level as an integer
        :rtype: int
        """
        if self == ProjectUserRole.OWNER:
            return 2  # Full access
        elif self == ProjectUserRole.USER:
            return 1  # Edit access
        else:
            return 0  # No access


class ProjectUserDTO(BaseModelDTO):
    """DTO for displaying project user information with their role."""

    user: UserDTO
    role: ProjectUserRole


class SaveProjectDTO(BaseModelDTO):
    name: str
    start_date: datetime
    end_date: datetime
    project_manager_id: str | None = None
    description: RichTextDTO | None = None


class CreateProjectFromTemplateDTO(BaseModelDTO):
    """DTO for creating a project from a template.

    role_mapping is a dictionary that maps template role names to user IDs.
    For example: {"project_manager": "user-id-123", "developer": "user-id-456"}
    """

    name: str
    start_date: datetime
    project_manager_id: str | None = None
    role_mapping: dict[str, str] | None = None


class AddTasksFromTemplateDTO(BaseModelDTO):
    """DTO for adding all the tasks of a project template into an existing project.

    role_mapping is a dictionary that maps template role names to user IDs.
    For example: {"project_manager": "user-id-123", "developer": "user-id-456"}
    """

    project_template_id: str
    start_date: datetime
    role_mapping: dict[str, str] | None = None


class ProjectDTO(ModelDTO):
    """DTO for displaying project information in the frontend."""

    title: str
    description: RichTextDTO | None
    start_date: datetime
    end_date: datetime
    # Pre-formatted server-side so the frontend never parses/reformats these dates itself.
    start_date_text: str
    end_date_text: str
    project_manager: UserDTO
    progress: int
    status: ProjectStatus
    created_by: UserDTO
    last_modified_by: UserDTO


class ProjectWithRootTasksDTO(BaseModelDTO):
    """DTO for displaying project information with its root tasks for GANTT chart view."""

    project: ProjectDTO
    root_tasks: list[TaskDTO]
