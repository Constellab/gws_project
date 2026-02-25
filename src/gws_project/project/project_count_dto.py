from gws_core import BaseModelDTO


class ProjectCountDTO(BaseModelDTO):
    """DTO for project count statistics for the current user."""

    total: int
    ongoing: int
    done: int
    todo: int


class ChildrenCountDTO(BaseModelDTO):
    """DTO for counting direct subtasks and documents of a project or task."""

    subtask_count: int
    document_count: int
