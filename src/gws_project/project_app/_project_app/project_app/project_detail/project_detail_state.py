import reflex as rx
from gws_core import RichTextDTO
from gws_project.project.project_count_dto import ChildrenCountDTO
from gws_project.project.project_dto import ProjectDTO, ProjectUserDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.project_app_router import ProjectAppRouter
from ..common.projects.project_page_state import ProjectPageState
from ..common.timestamp_text_component import format_timestamp
from ..common.view_mode_state import ViewModeState
from ..task_form.task_form_dialog_state import TaskFormDialogState
from ..task_list.task_list_state import TaskListState


class ProjectDetailState(rx.State):
    """State for managing the project detail page.

    This state handles fetching and displaying the details of a single project
    based on the project ID from the URL.
    """

    description_edit_mode: bool = False  # Track if description is in edit mode

    _project_id: str | None = None
    _project_users: list[ProjectUserDTO] = []

    # The project detail page only has these tabs. "activity" is only valid on the
    # task detail page, but ViewModeState is shared: navigating here after leaving a
    # task's Activity tab would otherwise carry that value over, matching none of
    # this page's tabs and rendering nothing.
    _valid_view_modes = ("list", "description", "documents")

    @rx.var
    async def view_mode(self) -> str:
        """Get the current view mode from ViewModeState.

        Falls back to "list" if the shared view mode isn't one of this page's tabs
        (e.g. "activity", carried over from a task detail page).

        :return: The current view mode
        :rtype: str
        """
        view_mode_state = await self.get_state(ViewModeState)
        mode = view_mode_state.view_mode

        if mode not in self._valid_view_modes:
            return "list"

        return mode

    @rx.var
    async def project(self) -> ProjectDTO | None:
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
    async def created_at_text(self) -> str:
        """Return the formatted creation timestamp of the current project.

        :return: The formatted timestamp, or "" if there is no current project
        :rtype: str
        """
        project = await self.project
        return format_timestamp(project.created_at) if project else ""

    @rx.var
    async def last_modified_at_text(self) -> str:
        """Return the formatted last-modified timestamp of the current project.

        :return: The formatted timestamp, or "" if there is no current project
        :rtype: str
        """
        project = await self.project
        return format_timestamp(project.last_modified_at) if project else ""

    @rx.var
    async def project_users(self) -> list[ProjectUserDTO]:
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
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                project_service = ProjectService()
                # Load project users
                project_users = project_service.get_project_users(current_project.id)
                self._project_users = [pu.to_dto() for pu in project_users]
            self._project_id = current_project.id

        return self._project_users

    @rx.var
    async def children_count(self) -> ChildrenCountDTO | None:
        """Get the number of tasks and documents for this project.

        :return: ChildrenCountDTO with subtask_count and document_count
        :rtype: Optional[ChildrenCountDTO]
        """
        project = await self.project
        if not project:
            return None

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            project_service = ProjectService()
            return project_service.get_project_children_count(project.id)

    async def reload_users(self):
        """Event handler called when the page loads.

        This method is automatically called by Reflex when the page is loaded.
        It extracts the project_id from the URL and loads the project.
        """
        self._project_id = None
        await self.project_users

    async def set_view_mode(self, value: str | list[str]):
        """Set the view mode by delegating to ViewModeState.

        :param value: The view mode value ("list", "description", or "documents")
        :type value: Union[str, List[str]]
        """
        view_mode_state = await self.get_state(ViewModeState)
        view_mode_state.set_view_mode(value)

    def toggle_description_edit_mode(self):
        """Toggle the description edit mode."""
        self.description_edit_mode = not self.description_edit_mode

    @rx.event
    async def handle_description_change(self, event_data: dict):
        """Handle changes from the rich text component and update the project description.

        Args:
            event_data: Dictionary containing the RichTextDTO data
        """
        # Convert event data to RichTextDTO
        description_dto = RichTextDTO.from_json(event_data)

        # Get current project
        project = await self.project
        if not project:
            return

        # Update the project description
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            project_service = ProjectService()
            project_service.update_project_description(project.id, description_dto)

        # Reload the project to reflect changes
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()

    async def open_create_task_dialog(self):
        """Open the create task dialog for this project."""
        form_state = await self.get_state(TaskFormDialogState)
        project = await self.project

        await form_state.open_create_dialog(
            project=project, callback_after_close=self._on_create_task_dialog_close
        )

    async def _on_create_task_dialog_close(self, task: Task):
        """Callback after the create task dialog is closed to refresh the task list.

        :param task: The created task
        :type task: Task
        """
        task_list_state = await self.get_state(TaskListState)
        await task_list_state.add_or_update_task(task)

    @rx.event
    async def open_delete_project_dialog(self):
        """Open the delete project confirmation dialog."""

        delete_dialog_state = await self.get_state(ConfirmDialogState)
        delete_dialog_state.open_dialog(
            title="Delete Project",
            content="Are you sure you want to delete this project? Its tasks, documents and notes will be permanently deleted. This action cannot be undone.",
            action=self._delete_project_action,
        )

    async def _delete_project_action(self):
        """Action to delete the project after confirmation."""
        project = await self.project
        if not project:
            yield
            return

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            project_service = ProjectService()
            project_service.delete_project(project.id)

        # Show success message
        yield rx.toast.success("Project deleted")

        # Redirect to project list
        yield rx.redirect(ProjectAppRouter.get_project_list_url())  # Assuming such a method exists
