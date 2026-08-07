from gws_core import ModelDTO, RichTextDTO, UserDTO


class TaskCommentDTO(ModelDTO):
    """DTO for displaying a task comment in the frontend."""

    task_id: str
    content: RichTextDTO | None
    created_by: UserDTO
    last_modified_by: UserDTO
    # True if the comment was edited after its creation (last_modified_at != created_at)
    is_edited: bool
