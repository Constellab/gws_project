

from datetime import datetime
from typing import Optional

from gws_core import BaseModelDTO, ModelDTO, UserDTO


class SaveProjectDTO(BaseModelDTO):
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    project_manager_id: Optional[str] = None


class ProjectDTO(ModelDTO):
    """DTO for displaying project information in the frontend."""
    title: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    project_manager: UserDTO
    created_by: UserDTO
    last_modified_by: UserDTO
