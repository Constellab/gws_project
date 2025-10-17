import reflex as rx
from gws_project.project.project_dto import ProjectUserDTO
from gws_project.project.project_service import ProjectService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from .project_detail_state import ProjectDetailState


class RemoveUserDialogState(ConfirmDialogState, ReflexMainState):
    """State for managing the remove user confirmation dialog.

    This state handles the confirmation dialog for removing users from a project.
    """

    user_to_remove: ProjectUserDTO = None

    @rx.event
    def open_dialog(self, user: ProjectUserDTO):
        """Open the confirmation dialog for removing a user.

        :param user: The user to remove
        :type user: ProjectUserDTO
        """
        self.user_to_remove = user
        self.dialog_opened = True

    @rx.event
    async def confirm_action(self):
        """Remove the user from the project."""
        if not self.user_to_remove:
            return

        try:
            with await self.authenticate_user():
                project_service = ProjectService()
                # Get the project ID from parent state
                project_detail_state = await self.get_state(ProjectDetailState)
                project_id = project_detail_state.get_project_id()

                # Remove the user from the project
                project_service.remove_user_from_project(project_id, self.user_to_remove.user.id)

            # Close the dialog
            self.close_dialog()
            self.user_to_remove = None

            # Reload the project users
            project_detail_state = await self.get_state(ProjectDetailState)
            await project_detail_state.load_project(project_detail_state.get_project_id())

            # Show success message
            return rx.toast.success("User removed from project successfully")

        except Exception as e:
            self.dialog_opened = False
            return rx.toast.error(f"Error removing user: {str(e)}")


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
