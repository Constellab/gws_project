

from typing import Optional

from gws_core import BaseModelDTO, ModelDTO, RichTextDTO, UserDTO


class SaveProjectTemplateDTO(BaseModelDTO):
    """DTO for creating a new project template"""
    name: str


class ProjectTemplateDTO(ModelDTO):
    """DTO for displaying project template information in the frontend"""
    name: str
    description: Optional[RichTextDTO]
    created_by: UserDTO
    last_modified_by: UserDTO
