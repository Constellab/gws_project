

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.user.user import User
from peewee import (CharField, DateField, DecimalField, ForeignKeyField,
                    TextField)

from .model_with_user import ModelWithUser


class Project(ModelWithUser):
    """
    Project model - Manages projects linked to companies

    Status values: 'active' (default), 'completed', 'archived', 'cancelled'
    """

    title = CharField(max_length=255, null=False)
    description = TextField(null=True)
    start_date = DateField(null=False, index=True)
    end_date = DateField(null=False, index=True)
    project_manager = ForeignKeyField(User, null=False)
    amount = DecimalField(max_digits=12, decimal_places=2, null=True)
    collaborative_folder_id = CharField(max_length=255, unique=True, null=True)

    class Meta:
        table_name = 'projects'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
