


from gws_core import BaseModelDTO, ModelDTO, RichTextDTO, UserDTO


class SaveProjectTemplateDTO(BaseModelDTO):
    """DTO for creating a new project template"""
    name: str


class ProjectTemplateDTO(ModelDTO):
    """DTO for displaying project template information in the frontend"""
    name: str
    description: RichTextDTO | None
    # Language-neutral fallback, replaced by the app layer with the creation date
    # in the user's language (see common/date_format.localize_project_template_dto).
    created_at_text: str
    created_by: UserDTO
    last_modified_by: UserDTO
