from typing import List

import reflex as rx
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.project_template_dto import ProjectTemplateDTO
from gws_project.template.project_template_service import \
    ProjectTemplateService
from gws_reflex_main import ReflexMainState

from ...common.project_app_router import ProjectAppRouter


class ProjectTemplateListState(ReflexMainState):
    """State for managing the template list page.

    This state handles fetching and displaying the list of project templates.
    """

    project_templates: List[ProjectTemplateDTO] = []
    is_loading: bool = False
    error_message: str = ""

    async def load_project_templates(self):
        """Load the list of project templates.

        This method fetches all project templates and converts them to DTOs
        for display in the frontend.
        """
        # Check authentication before accessing data
        if not await self.check_authentication():
            self.error_message = "You must be authenticated to view templates"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            templates: List[ProjectTemplate]
            with await self.authenticate_user():
                template_service = ProjectTemplateService()
                templates = template_service.get_all_templates()

            # Convert templates to DTOs
            self.project_templates = [template.to_dto() for template in templates]

        except Exception as e:
            self.error_message = f"Error loading templates: {str(e)}"
            self.project_templates = []

        finally:
            self.is_loading = False

    async def on_load(self):
        """Event handler called when the page loads.

        This method is automatically called by Reflex when the page is loaded.
        """
        await self.load_project_templates()

    @rx.event
    def go_to_project_template(self, project_template_id: str):
        """Navigate to the template detail page for the given template ID.

        :param template_id: The ID of the template to navigate to
        :type template_id: str
        """
        return rx.redirect(ProjectAppRouter.get_project_template_detail_url(project_template_id))

    @rx.event
    async def delete_project_template(self, template_id: str):
        """Delete a template.

        :param template_id: The ID of the template to delete
        :type template_id: str
        """
        try:
            with await self.authenticate_user():
                template_service = ProjectTemplateService()
                template_service.delete_project_template(template_id)

            # Reload templates after deletion
            await self.load_project_templates()

        except Exception as e:
            self.error_message = f"Error deleting template: {str(e)}"
