


from gws_core import BaseModelDTO, ModelDTO, RichTextDTO, UserDTO

from gws_project.task.task_dto import TaskPriority


class SaveTaskTemplateDTO(BaseModelDTO):
    """DTO for creating a new task template"""
    title: str
    start_date_offset: int | None = None
    duration_days: int | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    allow_subtasks: bool = False
    assign_to_role: str | None = None


class UpdateTaskTemplateDTO(BaseModelDTO):
    """DTO for updating an existing task template"""
    title: str
    start_date_offset: int | None
    duration_days: int | None
    priority: TaskPriority
    assign_to_role: str | None = None


class TaskTemplateDTO(ModelDTO):
    """DTO for displaying task template information in the frontend"""
    project_template_id: str
    parent_task_id: str | None
    title: str
    description: RichTextDTO | None
    start_date_offset: int | None
    duration_days: int | None
    priority: TaskPriority
    allow_subtasks: bool
    assign_to_role: str | None
    created_by: UserDTO
    last_modified_by: UserDTO
