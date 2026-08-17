from enum import Enum

from gws_core import TypedEnumField, TypedForeignKeyField

from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager

from .user import User


class AppRole(Enum):
    """Global, app-level role for gws_project.

    This is a new role concept, independent from ProjectUserRole (per-project
    access role) and from gws_core's UserGroup (lab-wide platform role).
    """

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class UserAppRole(ModelWithUser):
    """Stores the app-level role (Admin/Member) explicitly assigned to a user.

    A user with no row here defaults to AppRole.MEMBER (see AppRoleService).
    """

    user = TypedForeignKeyField(User, unique=True, backref="+")
    role = TypedEnumField(choices=AppRole, default=AppRole.MEMBER)

    class Meta:
        table_name = "gws_project_user_app_role"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
