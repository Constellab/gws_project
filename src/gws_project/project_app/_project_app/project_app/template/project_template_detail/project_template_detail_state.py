
import reflex as rx
from gws_core import RichTextDTO
from gws_project.template.project_template_dto import ProjectTemplateDTO
from gws_project.template.project_template_service import ProjectTemplateService
from gws_reflex_main import ReflexMainState

from ...common.project_app_router import ProjectAppRouter
from ..template_page_state import TemplatePageState


class TemplateDetailState(ReflexMainState):
    """State for managing the template detail page.

    This state handles loading and displaying template details,
    including description editing and delete operations.
    """

    # Delete confirmation dialog
    delete_dialog_opened: bool = False
    # Description edit mode
    description_edit_mode: bool = False
    # Cache for template roles
    _template_id: str | None = None
    _template_roles: list[str] = []

    def set_delete_dialog_opened(self, value: bool):
        """Explicitly set the delete_dialog_opened state.

        :param value: New value for delete_dialog_opened
        :type value: bool
        """
        self.delete_dialog_opened = value

    @rx.var
    async def project_template(self) -> ProjectTemplateDTO | None:
        """Get the current template as DTO.

        :return: The current template DTO
        :rtype: ProjectTemplateDTO
        """
        template_page_state = await self.get_state(TemplatePageState)
        current_object = await template_page_state.project_template()
        if current_object:
            return current_object.to_dto()
        return None

    @rx.var
    async def template_roles(self) -> list[str]:
        """Get all distinct roles from task templates in this project template.

        :return: List of distinct role names
        :rtype: List[str]
        """
        template = await self.project_template

        if not template:
            self._template_roles = []
            return []

        if self._template_id != template.id:
            with await self.authenticate_user():
                template_service = ProjectTemplateService()
                self._template_roles = template_service.get_all_roles_for_template(template.id)
            self._template_id = template.id

        return self._template_roles

    @rx.event
    def open_delete_template_dialog(self):
        """Open the delete confirmation dialog."""
        self.delete_dialog_opened = True

    @rx.event
    def close_delete_template_dialog(self):
        """Close the delete confirmation dialog."""
        self.delete_dialog_opened = False

    def toggle_description_edit_mode(self):
        """Toggle the description edit mode."""
        self.description_edit_mode = not self.description_edit_mode

    @rx.event
    async def delete_template(self):
        """Delete the current template and redirect to template list."""
        project_template = await self.project_template
        if not project_template:
            yield rx.toast.error("Template not found")
            return

        try:
            with await self.authenticate_user():
                template_service = ProjectTemplateService()
                template_service.delete_project_template(project_template.id)

            yield rx.toast.success("Template deleted successfully")
            yield rx.redirect(ProjectAppRouter.get_project_template_list_url())

        except Exception as e:
            yield rx.toast.error(f"Error deleting template: {str(e)}")

        finally:
            self.delete_dialog_opened = False

    @rx.event
    async def handle_description_change(self, event_data: dict):
        """Handle changes from the rich text component and update the template description.

        :param event_data: Dictionary containing the RichTextDTO data
        """
        project_template = await self.project_template
        if not project_template:
            yield rx.toast.error("Template not found")
            return

        # Convert event data to RichTextDTO
        description_dto = RichTextDTO.from_json(event_data)

        try:
            with await self.authenticate_user():
                template_service = ProjectTemplateService()
                template_service.update_template_description(
                    project_template.id,
                    description_dto
                )

            # Refresh the template
            template_page_state = await self.get_state(TemplatePageState)
            await template_page_state.refresh_object()

            yield rx.toast.success("Description updated successfully")

        except Exception as e:
            yield rx.toast.error(f"Error updating description: {str(e)}")

    @rx.event
    def init(self):
        """Initialize the state."""
        self.description_edit_mode = False
        self.delete_dialog_opened = False
