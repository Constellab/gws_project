from .user_app_role import AppRole, UserAppRole


class AppRoleService:
    """Service managing the app-level role (Admin/Member) of users.

    This role is independent from ProjectUserRole (per-project access) and
    from gws_core's UserGroup (lab-wide platform role): it only exists to
    gate app-specific admin features (e.g. working hours settings).
    """

    @classmethod
    def get_role_for_user(cls, user_id: str) -> AppRole:
        """Get the app role of a user, defaulting to MEMBER if never assigned."""
        user_app_role = UserAppRole.get_or_none(UserAppRole.user == user_id)
        return user_app_role.role if user_app_role else AppRole.MEMBER

    @classmethod
    def set_role_for_user(cls, user_id: str, role: AppRole) -> UserAppRole:
        """Create or update the app role of a user."""
        user_app_role = UserAppRole.get_or_none(UserAppRole.user == user_id)

        if not user_app_role:
            user_app_role = UserAppRole()
            user_app_role.user = user_id

        user_app_role.role = role
        return user_app_role.save()

    @classmethod
    def is_admin(cls, user_id: str) -> bool:
        """Check if a user has the Admin app role."""
        return cls.get_role_for_user(user_id) == AppRole.ADMIN
