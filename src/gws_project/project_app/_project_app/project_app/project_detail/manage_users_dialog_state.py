import reflex as rx
from gws_project.project.project_dto import ProjectUserDTO
from gws_project.project.project_service import ProjectService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.projects.project_page_state import ProjectPageState


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

    @rx.event
    async def open_remove_user_dialog(self, user: ProjectUserDTO):
        """Open the remove user confirmation dialog.

        :param user: The user to remove
        :type user: ProjectUserDTO
        """
        confirm_dialog_state = await self.get_state(ConfirmDialogState)

        # Store the user ID in a local variable that will be captured by the closure
        user_id = user.user.id
        user_name = f"{user.user.first_name} {user.user.last_name}"

        confirm_dialog_state.open_dialog(
            title="Remove User from Project",
            content=f"Are you sure you want to remove {user_name} from this project?",
            action=lambda: self._remove_user_action(user_id),
        )

    async def _remove_user_action(self, user_id: str):
        """Remove the user from the project."""
        project_page_state = await self.get_state(ProjectPageState)
        with await self.authenticate_user():
            project_service = ProjectService()
            # Get the project ID from parent state
            url_param = await project_page_state.get_url_params()

            # Remove the user from the project
            project_service.remove_user_from_project(url_param.id, user_id)

        # Reload the project users
        from .project_detail_state import ProjectDetailState

        detail_state = await self.get_state(ProjectDetailState)
        await detail_state.reload_users()

        # Show success message
        yield rx.toast.success("User removed from project successfully")
