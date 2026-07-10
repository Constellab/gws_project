from enum import Enum

from gws_core import ModelDTO, RichTextDTO, UserDTO


class ProjectDocumentType(Enum):
    """Type of a project document: an uploaded file or a rich-text note."""

    FILE = "FILE"
    NOTE = "NOTE"


class ProjectDocumentDTO(ModelDTO):
    """DTO for displaying a project document (file or note) in the frontend."""

    name: str
    type: ProjectDocumentType
    project_id: str
    task_id: str | None
    size: int | None  # file size in bytes, None for notes
    created_by: UserDTO
    last_modified_by: UserDTO


class ProjectNoteDTO(ProjectDocumentDTO):
    """DTO of a NOTE document including its rich-text content (note editor)."""

    content: RichTextDTO | None
