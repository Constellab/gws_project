

from typing import List

from .user import User


class UserService():
    """
    Service for managing users in the gws_project database.

    This service provides methods to retrieve users from the gws_project database
    and import users from gws_core when needed.
    """

    @classmethod
    def get_all_users(cls) -> List[User]:
        """
        Get all users from gws_project database.

        :return: List of all users in gws_project
        :rtype: List[User]
        """
        return list(User.select())

    @classmethod
    def get_user_by_id(cls, id_: str) -> User | None:
        """
        Get a user by ID from gws_project database.

        :param id_: The user ID to retrieve
        :type id_: str
        :return: The user if found, None otherwise
        :rtype: User | None
        """
        return User.get_by_id(id_)
