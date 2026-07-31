

from datetime import date
from enum import Enum

from gws_core import BaseModelDTO, ModelDTO, RichTextDTO, UserDTO


class TaskStatus(Enum):
    BACKLOG = 'BACKLOG'
    TODO = 'TODO'
    DOING = 'DOING'
    DONE = 'DONE'


class TaskPriority(Enum):
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'


class CreateTaskDTO(BaseModelDTO):
    title: str
    start_date: date | None
    end_date: date | None
    status: TaskStatus | None = TaskStatus.TODO
    priority: TaskPriority | None = TaskPriority.MEDIUM
    allow_subtasks: bool = False
    assign_to_id: str | None = None


class CreateSubTaskDTO(BaseModelDTO):
    title: str
    assign_to_id: str | None = None


class UpdateTaskDTO(BaseModelDTO):
    title: str
    start_date: date | None
    end_date: date | None
    status: TaskStatus | None
    priority: TaskPriority | None
    assign_to_id: str | None = None


class TaskDTO(ModelDTO):
    """DTO for displaying task information in the frontend."""
    title: str
    description: RichTextDTO | None
    start_date: date
    end_date: date
    status: TaskStatus
    priority: TaskPriority
    allow_subtasks: bool
    assign_to: UserDTO
    project_id: str
    parent_task_id: str | None
    parent_task_title: str | None
    progress: int
    created_by: UserDTO
    last_modified_by: UserDTO
