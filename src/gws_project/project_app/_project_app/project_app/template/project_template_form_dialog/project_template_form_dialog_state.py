
import reflex as rx
from gws_project.template.project_template_dto import ProjectTemplateDTO, SaveProjectTemplateDTO
from gws_project.template.project_template_service import ProjectTemplateService
from gws_reflex_main import FormDialogState, ReflexMainState

from ...common.project_app_router import ProjectAppRouter


class ProjectTemplateFormDialogState(FormDialogState, rx.State):
    """State management for the create/update template dialog functionality."""

    # Template being edited (None for create mode)
    _editing_template: ProjectTemplateDTO | None = None

    # Form field default values
    form_name: str = ""

    @rx.event
    async def open_update_dialog(self, template: ProjectTemplateDTO):
        """Open the dialog in update mode with existing template data.

        Args:
            template: The template to update
        """
        # Store the template being edited
        self._editing_template = template

        # Initialize form fields with template data
        self.form_name = template.name

        # Mark as editing
        self.is_update_mode = True

        # Open the dialog
        await self.open_dialog()

    def _validate_and_parse_form_data(self, form_data: dict) -> SaveProjectTemplateDTO | None:
        """Validate and parse form data into a template DTO.

        Args:
            form_data: Dictionary containing form fields (name)

        Returns:
            CreateProjectTemplateDTO if validation succeeds, None otherwise
        """
        # Get values from form data
        name = form_data.get('name', '').strip()

        # Validate required fields
        if not name:
            raise Exception("Template name is required")

        # Create and return the appropriate DTO
        return SaveProjectTemplateDTO(
            name=name,
        )

    async def _create(self, form_data: dict):
        """Create a new template using the form data.

        Args:
            form_data: Dictionary containing form fields (name)

        Yields:
            Reflex events (rx.toast, rx.redirect)
        """
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        # Validate and parse form data
        template_dto = self._validate_and_parse_form_data(form_data)
        if template_dto is None:
            return  # Validation error already shown

        # Create the template
        with await main_state.authenticate_user():
            template_service = ProjectTemplateService()
            created_template = template_service.create_project_template(template_dto)

        # Show success toast
        yield rx.toast.success("Template created successfully")

        # Redirect to the template list page
        yield rx.redirect(ProjectAppRouter.get_project_template_list_url())

    async def _update(self, form_data: dict):
        """Update an existing template using the form data.

        Args:
            form_data: Dictionary containing form fields (name)

        Yields:
            Reflex events (rx.toast)
        """
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        # Validate and parse form data
        template_dto = self._validate_and_parse_form_data(form_data)
        if template_dto is None:
            return  # Validation error already shown

        # Update the template
        with await main_state.authenticate_user():
            template_service = ProjectTemplateService()
            template_service.update_project_template(
                self._editing_template.id,
                template_dto
            )

        # Show success toast
        yield rx.toast.success("Template updated successfully")

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self._editing_template = None
        self.form_name = ""
        self.is_update_mode = False
