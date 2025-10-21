from datetime import datetime
from typing import Optional

import reflex as rx
from gws_project.project.project_dto import ProjectDTO, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_reflex_main import FormDialogState, ReflexMainState

from ..common.project_page_state import ProjectPageState


class ProjectFormDialogState(FormDialogState, rx.State):
    """State management for the create project dialog functionality."""

    # Project being edited (None for create mode)
    _editing_project: Optional[ProjectDTO] = None

    # Form field default values
    form_name: str = ""
    form_description: str = ""
    form_start_date: str = ""
    form_end_date: str = ""

    @rx.event
    async def open_update_dialog(self, project: ProjectDTO):
        """Open the dialog in update mode with existing project data.

        Args:
            project: The project to update
        """

        # Store the project being edited
        self._editing_project = project

        # Initialize form fields with project data
        self.form_name = project.title
        self.form_description = project.description or ""
        # set data to format 'YYYY-MM-DD' for date input
        self.form_start_date = project.start_date.strftime('%Y-%m-%d')
        self.form_end_date = project.end_date.strftime('%Y-%m-%d')

        # Mark as editing
        self.is_update_mode = True

        # Open the dialog
        await self.open_dialog()

    def _validate_and_parse_form_data(self, form_data: dict) -> Optional[SaveProjectDTO]:
        """Validate and parse form data into a SaveProjectDTO.

        Args:
            form_data: Dictionary containing form fields (name, description, start_date, end_date)

        Returns:
            SaveProjectDTO if validation succeeds, None otherwise (error toast is shown)
        """
        # Get values from form data
        name = form_data.get('name', '').strip()
        description = form_data.get('description', '').strip()
        start_date_str = form_data.get('start_date', '').strip()
        end_date_str = form_data.get('end_date', '').strip()

        # Validate required fields
        if not name:
            raise Exception("Project name is required")

        if not description:
            raise Exception("Project description is required")

        if not start_date_str:
            raise Exception("Start date is required")

        if not end_date_str:
            raise Exception("End date is required")

        # Parse dates from string to datetime
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        # Create and return the SaveProjectDTO
        return SaveProjectDTO(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            project_manager_id=None  # Using current user as project manager
        )

    async def _create(self, form_data: dict):
        """Create a new project using the form data.

        Args:
            form_data: Dictionary containing form fields (name, description, start_date, end_date)

        Yields:
            Reflex events (rx.toast, rx.redirect)
        """

        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        # Validate and parse form data
        project_dto = self._validate_and_parse_form_data(form_data)
        if project_dto is None:
            return  # Validation error already shown

        # Create the project
        with await main_state.authenticate_user():
            project_service = ProjectService()
            created_project = project_service.create_project(project_dto)

        # Show success toast
        yield rx.toast.success("Project created successfully")

        # Redirect to the project detail page
        yield rx.redirect(f"/project/{created_project.id}")

    async def _update(self, form_data: dict):
        """Update an existing project using the form data.

        Args:
            form_data: Dictionary containing form fields (name, description, start_date, end_date)

        Yields:
            Reflex events (rx.toast)
        """
        from ..project_detail.project_detail_state import ProjectDetailState

        main_state: ReflexMainState
        project_page_state: ProjectPageState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            project_page_state = await self.get_state(ProjectPageState)

        # Validate and parse form data
        project_dto = self._validate_and_parse_form_data(form_data)
        if project_dto is None:
            return  # Validation error already shown

        # Update the project
        with await main_state.authenticate_user():
            project_service = ProjectService()
            project_service.update_project(self._editing_project.id, project_dto)

        # Close dialog and clear all state after successful operation
        async with self:
            # Reload the project detail state if available
            project = await project_page_state.refresh_object()

        # Show success toast
        yield rx.toast.success("Project updated successfully")

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self._editing_project = None
        self.form_name = ""
        self.form_description = ""
        self.form_start_date = ""
        self.form_end_date = ""
        self.is_update_mode = False
