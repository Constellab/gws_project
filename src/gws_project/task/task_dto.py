

from datetime import date
from enum import Enum
from typing import Optional

from gws_core import BaseModelDTO, ModelDTO, UserDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO


class TaskStatus(Enum):
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
    assign_to_id: Optional[str] = None


class CreateSubTaskDTO(BaseModelDTO):
    title: str
    assign_to_id: Optional[str] = None


class UpdateTaskDTO(BaseModelDTO):
    title: str
    start_date: date | None
    end_date: date | None
    status: TaskStatus | None
    priority: TaskPriority | None


class TaskDTO(ModelDTO):
    """DTO for displaying task information in the frontend."""
    title: str
    description: Optional[RichTextDTO]
    start_date: date
    end_date: date
    status: TaskStatus
    priority: TaskPriority
    allow_subtasks: bool
    assign_to: UserDTO
    project_id: str
    parent_task_id: Optional[str]
    parent_task_title: Optional[str]
    space_folder_id: Optional[str]
    created_by: UserDTO
    last_modified_by: UserDTO
