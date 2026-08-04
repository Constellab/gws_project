


from gws_core import BaseModelDTO, ModelDTO, RichTextDTO, UserDTO


class SaveProjectTemplateDTO(BaseModelDTO):
    """DTO for creating a new project template"""
    name: str


class ProjectTemplateDTO(ModelDTO):
    """DTO for displaying project template information in the frontend"""
    name: str
    description: RichTextDTO | None
    # Pre-formatted server-side so the frontend never parses/reformats this date itself.
    created_at_text: str
    created_by: UserDTO
    last_modified_by: UserDTO
