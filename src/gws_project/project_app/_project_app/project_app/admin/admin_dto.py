from gws_core import BaseModelDTO, UserDTO
from gws_project.user.user_app_role import AppRole


class UserRowDTO(BaseModelDTO):
    """A user row for the Admin page's Roles section: identity + app role."""

    user: UserDTO
    role: AppRole
