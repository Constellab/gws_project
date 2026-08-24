
import reflex as rx
from gws_core import RichTextDTO
from gws_project.template.project_template_dto import ProjectTemplateDTO
from gws_project.template.project_template_service import ProjectTemplateService
from gws_reflex_main import I18nState, ReflexMainState, toast_tr

from ...common.project_app_router import ProjectAppRouter
from ...common.timestamp_text_component import format_timestamp
from ..template_page_state import TemplatePageState
from . import (
    project_template_detail_translations,  # noqa: F401  (side effect: registers translations)
)


class TemplateDetailState(rx.State):
    """State for managing the template detail page.

    This state handles loading and displaying template details,
    including description editing and delete operations.
    """

    # Delete confirmation dialog
    delete_dialog_opened: bool = False
    # Description edit mode
    description_edit_mode: bool = False
    # View mode for tabs
    view_mode: str = "task_templates"
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
    async def created_at_text(self) -> str:
        """Return the formatted creation timestamp of the current project template.

        :return: The formatted timestamp, or "" if there is no current template
        :rtype: str
        """
        project_template = await self.project_template
        if not project_template:
            return ""
        lang = (await self.get_state(I18nState)).lang
        return format_timestamp(project_template.created_at, lang)

    @rx.var
    async def last_modified_at_text(self) -> str:
        """Return the formatted last-modified timestamp of the current project template.

        :return: The formatted timestamp, or "" if there is no current template
        :rtype: str
        """
        project_template = await self.project_template
        if not project_template:
            return ""
        lang = (await self.get_state(I18nState)).lang
        return format_timestamp(project_template.last_modified_at, lang)

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
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
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
            yield await toast_tr.error(self, "project_template_detail.template_not_found")
            return

        try:
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                template_service = ProjectTemplateService()
                template_service.delete_project_template(project_template.id)

            yield await toast_tr.success(self, "project_template_detail.deleted_toast")
            yield rx.redirect(ProjectAppRouter.get_project_template_list_url())

        except Exception as e:
            yield await toast_tr.error(
                self, "project_template_detail.delete_error", {"error": str(e)}
            )

        finally:
            self.delete_dialog_opened = False

    @rx.event
    async def handle_description_change(self, event_data: dict):
        """Handle changes from the rich text component and update the template description.

        :param event_data: Dictionary containing the RichTextDTO data
        """
        project_template = await self.project_template
        if not project_template:
            yield await toast_tr.error(self, "project_template_detail.template_not_found")
            return

        # Convert event data to RichTextDTO
        description_dto = RichTextDTO.from_json(event_data)

        try:
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                template_service = ProjectTemplateService()
                template_service.update_template_description(
                    project_template.id,
                    description_dto
                )

            # Refresh the template
            template_page_state = await self.get_state(TemplatePageState)
            await template_page_state.refresh_object()

            yield await toast_tr.success(self, "project_template_detail.description_updated_toast")

        except Exception as e:
            yield await toast_tr.error(
                self, "project_template_detail.description_update_error", {"error": str(e)}
            )

    def set_view_mode(self, value: str | list[str]):
        """Set the view mode for the tabs.

        :param value: The view mode value
        :type value: Union[str, List[str]]
        """
        if isinstance(value, list):
            self.view_mode = value[0] if value else "task_templates"
        else:
            self.view_mode = value

    @rx.event
    def init(self):
        """Initialize the state."""
        self.description_edit_mode = False
        self.delete_dialog_opened = False
        self.view_mode = "task_templates"
