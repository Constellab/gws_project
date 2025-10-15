

from typing import List

from gws_core import EnumField
from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.task.task_dto import TaskPriority, TaskStatus
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
    def get_tasks_of_project(cls, project: 'Project') -> List['Task']:
        """Get all tasks associated with a project

        :param project: The project
        :type project: Project
        :return: List of tasks
        :rtype: List[Task]
        """
        return list(cls.select().where(cls.project == project).order_by(cls.created_at))

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

    class Meta:
        table_name = 'gws_project_tasks'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
