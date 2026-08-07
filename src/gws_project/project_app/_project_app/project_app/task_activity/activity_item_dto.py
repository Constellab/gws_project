from datetime import datetime

from gws_core import BaseModelDTO, RichTextDTO, UserDTO


class ActivityItemDTO(BaseModelDTO):
    """A single row of the task Activity timeline: either a history event or a comment.

    History events and comments come from two different backend tables; this DTO
    flattens both shapes into one so the timeline can render a single sorted,
    interleaved list (like a GitHub issue timeline).
    """

    id: str  # the underlying event/comment id, used as the foreach list key
    kind: str  # "event" or "comment"
    sort_key: datetime
    actor: UserDTO
    created_at_text: str

    # Event-only fields
    message: str | None = None
    icon: str | None = None
    is_automatic: bool = False

    # Comment-only fields
    comment_id: str | None = None
    content: RichTextDTO | None = None
    is_edited: bool = False
    can_edit: bool = False
