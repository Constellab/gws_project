from typing import List, Optional, Union

import reflex as rx
from gws_project.project.project_dto import ProjectDTO, ProjectUserDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.project_page_state import ProjectPageState
from ..task_form.task_form_dialog_state import TaskFormDialogState
from ..task_list.task_list_state import TaskListState


class ProjectDetailState(ReflexMainState):
    """State for managing the project detail page.

    This state handles fetching and displaying the details of a single project
    based on the project ID from the URL.
    """

    view_mode: str = "documents"  # "list", "kanban", or "documents"

    _project_id: Optional[str] = None
    _project_users: List[ProjectUserDTO] = []

    @rx.var
    async def project(self) -> Optional[ProjectDTO]:
        """Return the current project DTO.

        :return: The current project DTO
        :rtype: Optional[ProjectDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_object = await project_page_state.project()
        if current_object:
            return current_object.to_dto()
        return None

    @rx.var
    async def project_users(self) -> List[ProjectUserDTO]:
        """Return the list of project users associated with the current project.

        :return: List of ProjectUserDTOs
        :rtype: List[ProjectUserDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_project = await project_page_state.project()

        if not current_project:
            self._project_id = None
            self._project_users = []
            return []

        if self._project_id != current_project.id:
            with await self.authenticate_user():
                project_service = ProjectService()
                # Load project users
                project_users = project_service.get_project_users(current_project.id)
                self._project_users = [
                    pu.to_dto()
                    for pu in project_users
                ]
            self._project_id = current_project.id

        return self._project_users

    async def reload_users(self):
        """Event handler called when the page loads.

        This method is automatically called by Reflex when the page is loaded.
        It extracts the project_id from the URL and loads the project.
        """
        self._project_id = None
        await self.project_users

    def toggle_view_mode(self):
        """Toggle between list and kanban view modes."""
        self.view_mode = "kanban" if self.view_mode == "list" else "list"

    def set_view_mode(self, value: Union[str, List[str]]):
        """Set the view mode from the segmented control.

        :param value: The view mode value ("list" or "kanban")
        :type value: Union[str, List[str]]
        """
        # Handle both single value and list of values (though we only expect single)
        if isinstance(value, list):
            self.view_mode = value[0] if value else "list"
        else:
            self.view_mode = value

    async def open_create_task_dialog(self):
        """Open the create task dialog for this project."""
        form_state = await self.get_state(TaskFormDialogState)
        project = await self.project

        await form_state.open_create_dialog(
            project=project,
            callback_after_close=self._on_create_task_dialog_close
        )

    async def _on_create_task_dialog_close(self, task: Task):
        """Callback after the create task dialog is closed to refresh the task list.

        :param task: The created task
        :type task: Task
        """
        task_list_state = await self.get_state(TaskListState)
        task_list_state.add_or_update_task(task)

    @rx.event
    async def open_delete_project_dialog(self):
        """Open the delete project confirmation dialog."""

        delete_dialog_state = await self.get_state(ConfirmDialogState)
        delete_dialog_state.open_dialog(
            title="Delete Project",
            content="Are you sure you want to delete this project?",
            action=self._delete_project_action
        )

    async def _delete_project_action(self):
        """Action to delete the project after confirmation."""
        project = await self.project
        if not project:
            yield
            return

        with await self.authenticate_user():
            project_service = ProjectService()
            project_service.delete_project(project.id)

        # Show success message
        yield rx.toast.success("Project deleted")

        # Redirect to project list
        yield rx.redirect("/")
