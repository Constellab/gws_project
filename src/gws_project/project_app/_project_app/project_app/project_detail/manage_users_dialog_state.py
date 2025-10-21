from typing import AsyncGenerator

import reflex as rx
from gws_project.project.project_dto import ProjectUserDTO
from gws_project.project.project_service import ProjectService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.project_page_state import ProjectPageState


class RemoveUserDialogState(ConfirmDialogState, ReflexMainState):
    """State for managing the remove user confirmation dialog.

    This state handles the confirmation dialog for removing users from a project.
    """

    user_to_remove: ProjectUserDTO = None

    @rx.event
    def open_user_dialog(self, user: ProjectUserDTO):
        """Open the confirmation dialog for removing a user.

        :param user: The user to remove
        :type user: ProjectUserDTO
        """
        self.user_to_remove = user
        self.dialog_opened = True

    async def _on_confirm(self) -> AsyncGenerator:
        """Remove the user from the project."""
        if not self.user_to_remove:
            yield
            return

        project_page_state = await self.get_state(ProjectPageState)
        with await self.authenticate_user():
            project_service = ProjectService()
            # Get the project ID from parent state
            url_param = await project_page_state.get_url_params()

            # Remove the user from the project
            project_service.remove_user_from_project(url_param.id, self.user_to_remove.user.id)

        # Clear the user to remove
        async with self:
            self.user_to_remove = None

        # Reload the project users
        await project_page_state.refresh_object()

        # Show success message
        yield rx.toast.success("User removed from project successfully")


class ManageUsersDialogState(ReflexMainState):
    """State for managing the manage users dialog.

    This state handles the dialog open/close functionality for managing
    project users including viewing roles and performing actions on users.
    """

    dialog_opened: bool = False

    @rx.event
    def open_dialog(self):
        """Open the dialog."""
        self.dialog_opened = True

    @rx.event
    def close_dialog(self):
        """Close the dialog."""
        self.dialog_opened = False
