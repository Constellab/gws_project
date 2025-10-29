

from datetime import datetime
from enum import Enum
from typing import Optional

from gws_core import BaseModelDTO, ModelDTO, RichTextDTO, UserDTO


class ProjectUserRole(Enum):
    """Role of a user in a project - corresponds to Space folder user roles"""
    OWNER = 'OWNER'
    USER = 'USER'
    VIEWER = 'VIEWER'

    def get_access_level(self) -> int:
        """Get the access level corresponding to the role.

        :return: Access level as an integer
        :rtype: int
        """
        if self == ProjectUserRole.OWNER:
            return 3  # Full access
        elif self == ProjectUserRole.USER:
            return 2  # Edit access
        elif self == ProjectUserRole.VIEWER:
            return 1  # Read-only access
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
    project_manager_id: Optional[str] = None


class ProjectDTO(ModelDTO):
    """DTO for displaying project information in the frontend."""
    title: str
    description: Optional[RichTextDTO]
    start_date: datetime
    end_date: datetime
    project_manager: UserDTO
    created_by: UserDTO
    last_modified_by: UserDTO
