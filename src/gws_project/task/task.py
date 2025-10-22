

from typing import List

from gws_core import EnumField
from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.task.task_dto import TaskDTO, TaskPriority, TaskStatus
from gws_project.user.user import User
from peewee import (BooleanField, CharField, DateField, ForeignKeyField,
                    TextField)


class Task(ModelWithUser):
    """
    Task model - Manages tasks linked to projects

    Status values: 'TODO' (default), 'DOING', 'DONE',
    Priority values: 'HIGH', 'MEDIUM' (default), 'LOW'

    Business rules:
    - If allow_subtasks = TRUE: status calculated automatically from subtasks
    - If allow_subtasks = FALSE: status managed manually
    - The allow_subtasks field cannot be modified after creation
    """

    project = ForeignKeyField(Project, on_delete='CASCADE', null=False, backref='+')
    parent_task: 'Task' = ForeignKeyField('self', on_delete='CASCADE', null=True, backref='subtasks')
    title = CharField(max_length=255, null=False)
    description = TextField(null=True)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    status = EnumField(choices=TaskStatus, max_length=20, default=TaskStatus.TODO, null=False)
    priority = EnumField(choices=TaskPriority, max_length=10, default=TaskPriority.MEDIUM, null=False)
    allow_subtasks = BooleanField(default=False)
    assign_to = ForeignKeyField(User, null=False, backref='+')
    space_folder_id = CharField(max_length=36, unique=True, null=True)

    subtasks: List['Task']

    def is_root_task(self) -> bool:
        """Check if the task is a root task (i.e., has no parent task)"""
        return self.parent_task is None

    def is_leaf_task(self) -> bool:
        """Check if the task is a leaf task (i.e., has no subtasks)"""
        return not self.allow_subtasks

    def get_subtasks(self) -> List['Task']:
        """Get the list of subtasks for this task"""
        return self.subtasks

    @classmethod
    def get_root_tasks_of_project(cls, project_id: str) -> List['Task']:
        """Get all tasks associated with a project

        :param project: The project
        :type project: Project
        :return: List of tasks
        :rtype: List[Task]
        """
        return list(cls.select().where((cls.project == project_id) & (cls.parent_task.is_null())).order_by(cls.created_at))

    @classmethod
    def get_subtasks_of_task(cls, parent_task_id: str) -> List['Task']:
        """Get all subtasks of a parent task

        :param parent_task: The parent task
        :type parent_task: Task
        :return: List of subtasks
        :rtype: List[Task]
        """
        return list(cls.select().where(cls.parent_task == parent_task_id).order_by(cls.created_at))

    @classmethod
    def get_tasks_of_user(cls, user_id: str) -> List['Task']:
        """Get all tasks assigned to a user

        :param user_id: The user ID
        :type user_id: str
        :return: List of tasks
        :rtype: List[Task]
        """
        return list(cls.select().where(cls.assign_to == user_id).order_by(cls.created_at))

    @classmethod
    def count_tasks_of_user_in_project(cls, user_id: str, project_id: str) -> int:
        """Count all tasks assigned to a user in a specific project

        :param user_id: The user ID
        :type user_id: str
        :return: Count of tasks
        :rtype: int
        """
        return cls.select().where((cls.assign_to == user_id) & (cls.project == project_id)).count()

    def to_dto(self) -> TaskDTO:
        """Convert the Task model to a TaskDTO for display in the frontend.

        :return: TaskDTO instance
        :rtype: TaskDTO
        """
        return TaskDTO(
            id=self.id,
            title=self.title,
            description=self.description,
            start_date=self.start_date,
            end_date=self.end_date,
            status=self.status,
            priority=self.priority,
            allow_subtasks=self.allow_subtasks,
            assign_to=self.assign_to.to_dto(),
            project_id=self.project.id,
            parent_task_id=self.parent_task.id if self.parent_task else None,
            parent_task_title=self.parent_task.title if self.parent_task else None,
            space_folder_id=self.space_folder_id,
            created_at=self.created_at,
            created_by=self.created_by.to_dto(),
            last_modified_at=self.last_modified_at,
            last_modified_by=self.last_modified_by.to_dto()
        )

    class Meta:
        table_name = 'gws_project_tasks'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
