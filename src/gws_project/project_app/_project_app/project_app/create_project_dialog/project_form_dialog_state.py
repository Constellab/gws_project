from datetime import datetime
from typing import Callable, Optional

import reflex as rx
from gws_core import Logger
from gws_project.project.project_dto import ProjectDTO, SaveProjectDTO
from gws_project.project.project_service import ProjectService

from ..project_list.project_list_state import ProjectListState


class ProjectFormDialogState(rx.State):
    """State management for the create project dialog functionality."""

    # Dialog state
    dialog_opened: bool = False

    # Project being edited (None for create mode)
    _editing_project: Optional[ProjectDTO] = None

    # Form field default values
    form_name: str = ""
    form_description: str = ""
    form_start_date: str = ""
    form_end_date: str = ""

    def open_dialog(self):
        """Open the create project dialog.

        Args:
            on_close: Optional callback function to call when dialog is closed
        """
        # Reset form fields for create mode
        self._editing_project = None
        self.form_name = ""
        self.form_description = ""
        self.form_start_date = ""
        self.form_end_date = ""
        self.dialog_opened = True

    def open_update_dialog(self, project: ProjectDTO):
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

        # Open the dialog
        self.dialog_opened = True

    @rx.event
    async def close_dialog(self):
        """Close the create project dialog and call the callback if provided."""
        # Call the callback function if it exists

        # Clear all state
        self.dialog_opened = False
        self._editing_project = None
        self.form_name = ""
        self.form_description = ""
        self.form_start_date = ""
        self.form_end_date = ""

    @rx.event()
    async def submit_form(self, form_data: dict):
        """Create or update a project using the form data.

        This is a background task that handles project creation/update asynchronously.
        The operation (create vs update) is determined by whether editing_project is set.

        Args:
            form_data: Dictionary containing form fields (name, description, start_date, end_date)
        """
        from ..project_detail.project_detail_state import ProjectDetailState

        project_list_state: ProjectListState

        # Get parent state instance
        project_list_state = await self.get_state(ProjectListState)


        try:
            # Get values from form data
            name = form_data.get('name', '').strip()
            description = form_data.get('description', '').strip()
            start_date_str = form_data.get('start_date', '').strip()
            end_date_str = form_data.get('end_date', '').strip()

            # Validate required fields
            if not name:
                return rx.toast.error("Project name is required")

            if not description:
                return rx.toast.error("Project description is required")

            if not start_date_str:
                return rx.toast.error("Start date is required")

            if not end_date_str:
                return rx.toast.error("End date is required")

            # Parse dates from string to datetime
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)

            # Create the SaveProjectDTO
            project_dto = SaveProjectDTO(
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                project_manager_id=None  # Using current user as project manager
            )

            # Determine if we're creating or updating
            is_update = self._editing_project is not None

            # Create or update the project
            with await project_list_state.authenticate_user():
                project_service = ProjectService()
                if is_update:
                    project_service.update_project(self._editing_project.id, project_dto)
                else:
                    project_service.create_project(project_dto)

            # Reload projects in the list state
            await project_list_state.load_projects()

            # If we're updating, also reload the project detail state if available
            if is_update:
                try:
                    project_detail_state = await self.get_state(ProjectDetailState)
                    if project_detail_state._project_id == self._editing_project.id:
                        await project_detail_state.load_project(self._editing_project.id)
                except Exception:
                    # Project detail state may not exist if we're on the list page
                    pass


            # Close dialog and clear all state after successful operation
            self.dialog_opened = False
            self._editing_project = None
            self.form_name = ""
            self.form_description = ""
            self.form_start_date = ""
            self.form_end_date = ""

            # Show success toast
            success_message = "Project updated successfully" if is_update else "Project created successfully"
            return rx.toast.success(success_message)

        except ValueError as e:
            Logger.log_exception_stack_trace(e)
            return rx.toast.error(f"Invalid date format: {str(e)}")
        except Exception as e:
            Logger.log_exception_stack_trace(e)
            operation = "updating" if self._editing_project is not None else "creating"
            return rx.toast.error(f"Error {operation} project: {str(e)}")
