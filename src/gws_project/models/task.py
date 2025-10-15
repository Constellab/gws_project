

from typing import List

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.user.user import User
from peewee import (BooleanField, CharField, DateField, ForeignKeyField,
                    IntegerField, TextField)

from .model_with_user import ModelWithUser
from .project import Project


class Task(ModelWithUser):
    """
    Task model - Manages tasks linked to projects

    Status values: 'todo' (default), 'doing', 'done', 'blocked'
    Priority values: 'high', 'medium' (default), 'low'

    Business rules:
    - If allow_subtasks = TRUE: status calculated automatically from subtasks
    - If allow_subtasks = FALSE: status managed manually
    - The allow_subtasks field cannot be modified after creation
    """

    project = ForeignKeyField(Project, on_delete='CASCADE', null=False, backref='+')
    parent_task = ForeignKeyField('self', on_delete='CASCADE', null=True, backref='subtasks')
    title = CharField(max_length=255, null=False)
    description = TextField(null=True)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    status = CharField(max_length=20, default='todo', null=False)
    priority = CharField(max_length=10, default='medium', null=False)
    allow_subtasks = BooleanField(default=False)
    assign_to = ForeignKeyField(User, null=False, backref='+')

    subtasks: List['Task']

    class Meta:
        table_name = 'tasks'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
