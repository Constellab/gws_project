

from typing import List

from gws_core import Logger
from gws_core import User as GwsCoreUser
from gws_core import UserService as GwsCoreUserService
from gws_project.user.user import User


class UserService():

    @classmethod
    def sync_users(cls) -> None:
        """
        Synchronize users from gws_core to gws_project database.
        Retrieves all users from gws_core UserService and creates or updates them in gws_project.
        """
        Logger.debug("[GWS_PROJECT] Starting user synchronization from gws_core to gws_project")

        try:
            # Get all users from gws_core
            gws_core_users = GwsCoreUserService.get_all_users()
            errors = []

            for gws_core_user in gws_core_users:
                try:
                    cls.sync_gws_core_user(gws_core_user)
                except Exception as e:
                    error_msg = f"Error syncing user {gws_core_user.email}: {str(e)}"
                    Logger.error(error_msg)
                    errors.append(error_msg)

            Logger.debug(
                f"[GWS_PROJECT] User synchronization completed"
            )

            if errors:
                Logger.warning(f"[GWS_PROJECT] Encountered {len(errors)} errors during synchronization")

        except Exception as err:
            Logger.error(f"[GWS_PROJECT] Fatal error during user synchronization: {err}")

    @classmethod
    def sync_gws_core_user(cls, gws_core_user: GwsCoreUser) -> User:
        # Check if user already exists in gws_project
        project_user = User.get_by_id(gws_core_user.id)

        force_insert = False
        if project_user is None:
            # Create new user in gws_project
            project_user = User(
                id=gws_core_user.id
            )
            force_insert = True

        project_user.created_at = gws_core_user.created_at
        project_user.last_modified_at = gws_core_user.last_modified_at
        project_user.email = gws_core_user.email
        project_user.first_name = gws_core_user.first_name
        project_user.last_name = gws_core_user.last_name
        project_user.group = gws_core_user.group
        project_user.is_active = gws_core_user.is_active
        project_user.photo = gws_core_user.photo

        return project_user.save(force_insert=force_insert)


    @classmethod
    def get_all_users(cls) -> List[User]:
        """Get all users from gws_project database"""
        return list(User.select())

    @classmethod
    def get_user_by_id(cls, id_: str) -> User | None:
        """Get a user by ID from gws_project database"""
        return User.get_by_id(id_)
