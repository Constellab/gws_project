

from enum import Enum
from typing import Union

from gws_core import EnumField
from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.user.user import User
from peewee import ForeignKeyField

from .project import Project


class ProjectUserRole(Enum):
    """Role of a user in a project - corresponds to Space folder user roles"""
    OWNER = 'OWNER'
    USER = 'USER'
    VIEWER = 'VIEWER'

    def get_access_level(self) -> int:
        """Get the access level corresponding to the role.

        :return: Access level as an integer
        :rtype: int
        """
        if self == ProjectUserRole.OWNER:
            return 3  # Full access
        elif self == ProjectUserRole.USER:
            return 2  # Edit access
        elif self == ProjectUserRole.VIEWER:
            return 1  # Read-only access
        else:
            return 0  # No access


class ProjectUser(ModelWithUser):
    """
    Project User model - Junction table for users assigned to projects

    Note: This model extends Model instead of ModelWithUser because it has
    assigned_at and assigned_by fields instead of created_at/created_by
    """

    project = ForeignKeyField(Project, on_delete='CASCADE', null=False, backref='+')
    user = ForeignKeyField(User, null=False, backref='+')
    role: ProjectUserRole = EnumField(choices=ProjectUserRole,
                                      max_length=20,
                                      null=False,
                                      default=ProjectUserRole.USER.value)

    @classmethod
    def get_users_of_project(cls, project_id: str) -> list[User]:
        """Get the list of user IDs that are members of a project.

        :param project: The project
        :type project: Project
        :return: List of user IDs
        :rtype: list[str]
        """
        return [pu.user for pu in cls.select().where(cls.project == project_id)]

    @classmethod
    def get_projects_of_user(cls, user_id: str) -> list[Project]:
        """Get the list of projects that a user is a member of.

        :param user_id: The user ID
        :type user_id: str
        :return: List of projects
        :rtype: list[Project]
        """
        return [pu.project for pu in cls.select().where(cls.user == user_id)]

    @classmethod
    def is_user_in_project(cls, project_id: str, user_id: str) -> bool:
        """Check if a user is a member of a project.

        :param project: The project
        :type project: Project
        :param user_id: The user ID to check
        :type user_id: str
        :return: True if the user is a member, False otherwise
        :rtype: bool
        """
        return cls.select().where(
            (cls.project == project_id) & (cls.user == user_id)
        ).exists()

    @classmethod
    def user_has_role(cls, project_id: str, user_id: str, role: ProjectUserRole) -> bool:
        """Check if a user has a specific role or higher in a project.
        :param project: The project
        :type project: Project
        :param user_id: The user ID to check
        :type user_id: str
        :param role: The role to check
        :type role: ProjectUserRole
        :return: True if the user has the role, False otherwise
        :rtype: bool
        """
        project_user = cls.get_by_project_and_user(project_id, user_id)

        if not project_user:
            return False

        return project_user.role.get_access_level() >= role.get_access_level()

    @classmethod
    def get_by_project_and_user(cls, project_id: str, user_id: str) -> Union['ProjectUser', None]:
        """Get the ProjectUser entity for a given project and user.

        :param project: The project
        :type project: Project
        :param user_id: The user ID
        :type user_id: str
        :return: The ProjectUser entity
        :rtype: ProjectUser
        :raises DoesNotExist: If no such ProjectUser exists
        """
        return cls.get_or_none(
            (cls.project == project_id) & (cls.user == user_id)
        )

    @classmethod
    def count_owner_by_project(cls, project_id: str) -> int:
        """Count the number of owners in a project.

        :param project_id: The project ID
        :type project_id: str
        :return: The count of owners
        :rtype: int
        """
        return cls.select().where(
            (cls.project == project_id) & (cls.role == ProjectUserRole.OWNER.value)
        ).count()

    class Meta:
        table_name = 'gws_project_project_users'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
        indexes = (
            (('project_id', 'user_id'), True),  # Unique constraint on (project_id, user_id)
        )
