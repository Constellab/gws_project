

from datetime import date
from enum import Enum
from typing import Optional

from gws_core import BaseModelDTO
from gws_project.user.user import User


class TaskStatus(Enum):
    TODO = 'TODO'
    DOING = 'DOING'
    DONE = 'DONE'


class TaskPriority(Enum):
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'


class CreateRootTaskDTO(BaseModelDTO):
    title: str
    description: str
    start_date: date
    end_date: date
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    allow_subtasks: bool = False
    assign_to_id: Optional[str] = None


class CreateSubTaskDTO(BaseModelDTO):
    title: str
    description: str
    start_date: date
    end_date: date
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assign_to_id: Optional[str] = None


class UpdateTaskDTO(BaseModelDTO):
    title: str
    description: str
    start_date: date
    end_date: date
    priority: TaskPriority
