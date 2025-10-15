

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.models.model_with_user import ModelWithUser
from gws_project.user.user import User
from peewee import ForeignKeyField

from .project import Project


class ProjectUser(ModelWithUser):
    """
    Project User model - Junction table for users assigned to projects

    Note: This model extends Model instead of ModelWithUser because it has
    assigned_at and assigned_by fields instead of created_at/created_by
    """

    project = ForeignKeyField(Project, on_delete='CASCADE', null=False, backref='+')
    user = ForeignKeyField(User, null=False, backref='+')

    class Meta:
        table_name = 'project_users'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
        indexes = (
            (('project_id', 'user_id'), True),  # Unique constraint on (project_id, user_id)
        )
