from typing import Optional

import reflex as rx
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_reflex_main import FormDialogState, ReflexMainState

from ..common.project_page_state import ProjectPageState


class ProjectDescriptionDialogState(FormDialogState, rx.State):
    """State management for the project description dialog functionality."""

    # Project being edited
    _project_id: Optional[str] = None

    # Form field default values
    form_description_rich_text: Optional[RichTextDTO] = None

    @rx.event
    def handle_description_change(self, event_data: dict):
        """Handle changes from the rich text component.

        Args:
            event_data: Dictionary containing the RichTextDTO data
        """
        # Store the rich text as DTO
        self.form_description_rich_text = RichTextDTO.from_json(event_data)

    @rx.event
    async def open_dialog_with_project(self, project: ProjectDTO):
        """Open the dialog with existing project description.

        Args:
            project: The project to edit description for
        """
        # Store the project ID
        self._project_id = project.id

        # Initialize form fields with project data
        self.form_description_rich_text = project.description

        # Mark as update mode (always updating description)
        self.is_update_mode = True

        # Open the dialog
        await self.open_dialog()

    async def _create(self, form_data: dict):
        """Not used for description updates."""
        pass

    async def _update(self, form_data: dict):
        """Update the project description.

        Args:
            form_data: Dictionary containing form fields (not used, we use state variables)

        Yields:
            Reflex events (rx.toast)
        """
        main_state: ReflexMainState
        project_page_state: ProjectPageState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            project_page_state = await self.get_state(ProjectPageState)

        # Update the project description
        with await main_state.authenticate_user():
            project_service = ProjectService()
            project_service.update_project_description(
                self._project_id,
                self.form_description_rich_text
            )

        # Reload the project detail state
        async with self:
            await project_page_state.refresh_object()

        # Show success toast
        yield rx.toast.success("Project description updated successfully")

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self._project_id = None
        self.form_description_rich_text = None
        self.is_update_mode = False
