

from gws_core import RichText, TypedCharField, TypedRichTextDbField

from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.template.project_template_dto import ProjectTemplateDTO


class ProjectTemplate(ModelWithUser):
    """
    Template for creating projects with predefined task structures

    Templates allow users to quickly create projects with a standardized
    set of tasks and subtasks based on common project types.
    """

    name = TypedCharField(max_length=255, unique=True)
    description = TypedRichTextDbField()

    def to_dto(self) -> ProjectTemplateDTO:
        """Convert the ProjectTemplate model to a DTO for display in the frontend.

        :return: ProjectTemplateDTO instance
        :rtype: ProjectTemplateDTO
        """
        return ProjectTemplateDTO(
            id=self.id,
            name=self.name,
            description=self.description,
            created_at=self.created_at,
            created_at_text=self.created_at.strftime("%b %d, %Y"),
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
        )

    def get_rich_text(self) -> RichText:
        """Get the rich text description of the template.

        :return: RichTextDTO of the description
        :rtype: RichTextDTO
        """
        return RichText(self.description)

    def has_description(self) -> bool:
        """Check if the template has a non-empty description.

        :return: True if description exists and is not empty, False otherwise
        :rtype: bool
        """
        return not self.get_rich_text().is_empty()

    class Meta:
        table_name = 'gws_project_project_templates'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
