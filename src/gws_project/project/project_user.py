from typing import Union

from gws_core import TypedEnumField, TypedForeignKeyField

from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project_dto import ProjectUserDTO, ProjectUserRole
from gws_project.user.user import User

from .project import Project


class ProjectUser(ModelWithUser):
    """
    Project User model - Junction table for users assigned to projects

    Note: This model extends Model instead of ModelWithUser because it has
    assigned_at and assigned_by fields instead of created_at/created_by
    """

    project = TypedForeignKeyField(Project, on_delete="CASCADE", backref="+")
    user = TypedForeignKeyField(User, backref="+")
    role = TypedEnumField(
        choices=ProjectUserRole, max_length=20, default=ProjectUserRole.USER.value
    )

    def to_dto(self) -> ProjectUserDTO:
        """Convert the ProjectUser model to a ProjectUserDTO.

        :return: The ProjectUserDTO representation
        :rtype: ProjectUserDTO
        """
        return ProjectUserDTO(user=self.user.to_dto(), role=self.role)

    @classmethod
    def get_by_project(cls, project_id: str) -> list["ProjectUser"]:
        """Get the list of ProjectUser entities for a given project.

        :param project: The project
        :type project: Project
        :return: List of ProjectUser entities
        :rtype: list[ProjectUser]
        """
        return list(cls.select().where(cls.project == project_id))

    @classmethod
    def get_users_of_project(cls, project_id: str) -> list[User]:
        """Get the list of user IDs that are members of a project.

        :param project: The project
        :type project: Project
        :return: List of user IDs
        :rtype: list[str]
        """
        return [user.user for user in cls.get_by_project(project_id)]

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
        return cls.select().where((cls.project == project_id) & (cls.user == user_id)).exists()

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
    def get_by_project_and_user(cls, project_id: str, user_id: str) -> Union["ProjectUser", None]:
        """Get the ProjectUser entity for a given project and user.

        :param project: The project
        :type project: Project
        :param user_id: The user ID
        :type user_id: str
        :return: The ProjectUser entity
        :rtype: ProjectUser
        :raises DoesNotExist: If no such ProjectUser exists
        """
        return cls.get_or_none((cls.project == project_id) & (cls.user == user_id))

    @classmethod
    def count_owner_by_project(cls, project_id: str) -> int:
        """Count the number of owners in a project.

        :param project_id: The project ID
        :type project_id: str
        :return: The count of owners
        :rtype: int
        """
        return cls.select().where((cls.project == project_id) & (cls.role == ProjectUserRole.OWNER.value)).count()

    @classmethod
    def create_or_update(cls, project: Project, user: User, role: ProjectUserRole) -> "ProjectUser":
        """Create or update a ProjectUser entity.

        :param project: The project
        :type project: Project
        :param user: The user
        :type user: User
        :param role: The role to assign
        :type role: ProjectUserRole
        :param assigned_by: The user assigning the role
        :type assigned_by: User, optional
        :return: The created or updated ProjectUser entity
        :rtype: ProjectUser
        """
        project_user = cls.get_by_project_and_user(project.id, user.id)

        if not project_user:
            project_user = cls()
            project_user.project = project
            project_user.user = user

        project_user.role = role
        project_user.save()

        return project_user

    class Meta:
        table_name = "gws_project_project_users"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
        indexes = (
            (("project_id", "user_id"), True),  # Unique constraint on (project_id, user_id)
        )
