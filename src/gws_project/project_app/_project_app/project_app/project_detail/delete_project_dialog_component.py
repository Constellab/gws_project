from typing import AsyncGenerator

import reflex as rx
from gws_project.project.project_service import ProjectService
from gws_reflex_main import ConfirmDialogState, ReflexMainState, confirm_dialog


class DeleteProjectDialogState(ConfirmDialogState, rx.State):

    _project_id: str = ""

    @rx.event
    def open_dialog_with_project(self, project_id: str):
        """Open the delete confirmation dialog.

        :param project_id: The ID of the project to delete
        :type project_id: str
        :param project_title: The title of the project (for display)
        :type project_title: str
        """
        self._project_id = project_id
        self.open_dialog()

    async def _on_confirm(self) -> AsyncGenerator:
        if not self._project_id:
            yield
            return

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            project_service = ProjectService()
            project_service.delete_project(self._project_id)

        # Show success message
        yield rx.toast.success(f"Project deleted")

        # Clear the project ID
        async with self:
            self._project_id = ""

        # Redirect to project list
        yield rx.redirect("/")


def delete_project_dialog() -> rx.Component:
    """Dialog component for confirming project deletion.

    Displays a warning message and asks for user confirmation before
    deleting the project. Shows the project title in the message.
    Uses the reusable confirm_dialog component from gws_reflex_main.

    :return: The delete project dialog component
    :rtype: rx.Component
    """

    return confirm_dialog(
        state=DeleteProjectDialogState,
        title="Delete Project",
        content="Are you sure you want to delete this project?"
    )
