

from typing import List

from gws_core import BadRequestException, RichText, RichTextDTO
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.project_template_dto import SaveProjectTemplateDTO
from gws_project.template.task_template import TaskTemplate


class ProjectTemplateService:
    """Service class for managing project templates and task templates.

    This service provides methods to create, update, and delete project templates,
    as well as manage the task templates associated with them.
    """

    def get_template(self, template_id: str) -> ProjectTemplate:
        """Get a project template by ID.

        :param template_id: The ID of the template to retrieve
        :type template_id: str
        :return: The project template
        :rtype: ProjectTemplate
        :raises NotFoundException: If the template is not found
        """
        return ProjectTemplate.get_by_id_and_check(template_id)

    def get_all_templates(self) -> List[ProjectTemplate]:
        """Get all project templates.
        :return: List of all project templates
        :rtype: List[ProjectTemplate]
        """
        query = ProjectTemplate.select()
        return list(query.order_by(ProjectTemplate.created_at.desc()))

    def get_task_templates_for_template(self, template_id: str) -> List[TaskTemplate]:
        """Get all root task templates for a project template.

        :param template_id: The ID of the project template
        :type template_id: str
        :return: List of root task templates
        :rtype: List[TaskTemplate]
        """
        # Verify template exists
        ProjectTemplate.get_by_id_and_check(template_id)

        return TaskTemplate.get_root_tasks_of_template(template_id)

    @ProjectDbManager.transaction()
    def create_project_template(self, template_dto: SaveProjectTemplateDTO) -> ProjectTemplate:
        """Create a new project template.

        :param template_dto: The template data to create
        :type template_dto: CreateProjectTemplateDTO
        :return: The created project template
        :rtype: ProjectTemplate
        :raises BadRequestException: If a template with the same name already exists
        """
        # Check if a template with the same name already exists
        existing_template = ProjectTemplate.select().where(
            ProjectTemplate.name == template_dto.name
        ).first()

        if existing_template:
            raise BadRequestException(
                f"A template with the name '{template_dto.name}' already exists."
            )

        # Create the template
        template = ProjectTemplate()
        template.name = template_dto.name
        template.description = RichText().to_dto()  # Initialize with empty rich text

        # Save to database
        template.save()

        return template

    @ProjectDbManager.transaction()
    def update_project_template(self, template_id: str,
                                template_dto: SaveProjectTemplateDTO) -> ProjectTemplate:
        """Update an existing project template.

        :param template_id: The ID of the template to update
        :type template_id: str
        :param template_dto: The updated template data
        :type template_dto: SaveProjectTemplateDTO
        :return: The updated project template
        :rtype: ProjectTemplate
        :raises NotFoundException: If the template is not found
        :raises BadRequestException: If the new name conflicts with another template
        """
        # Get the template
        template = ProjectTemplate.get_by_id_and_check(template_id)

        # Check if the new name conflicts with another template
        if template.name != template_dto.name:
            existing_template = ProjectTemplate.select().where(
                (ProjectTemplate.name == template_dto.name) &
                (ProjectTemplate.id != template_id)
            ).first()

            if existing_template:
                raise BadRequestException(
                    f"A template with the name '{template_dto.name}' already exists."
                )

        # Update the template fields
        template.name = template_dto.name

        # Save to database
        template.save()

        return template

    @ProjectDbManager.transaction()
    def delete_project_template(self, template_id: str) -> None:
        """Delete a project template and all its associated task templates.

        The cascade delete will automatically remove all task templates
        associated with this project template.

        :param template_id: The ID of the template to delete
        :type template_id: str
        :raises NotFoundException: If the template is not found
        """
        # Get the template
        template = ProjectTemplate.get_by_id_and_check(template_id)

        # Delete the template (cascade will delete task templates)
        template.delete_instance()

    @ProjectDbManager.transaction()
    def update_template_description(self, template_id: str, description: RichTextDTO) -> ProjectTemplate:
        """Update a project template's description.

        :param template_id: The ID of the template
        :type template_id: str
        :param description: The new rich text description
        :type description: RichTextDTO
        :return: The updated template
        :rtype: ProjectTemplate
        """
        # Get the template
        template = ProjectTemplate.get_by_id_and_check(template_id)

        # Update the description
        template.description = description
        template.save()

        return template

    def get_all_roles_for_template(self, template_id: str) -> List[str]:
        """Get all distinct assign_to_role values from all task templates in a project template.

        :param template_id: The ID of the project template
        :type template_id: str
        :return: List of distinct role names (excluding None values)
        :rtype: List[str]
        """
        # Verify template exists
        ProjectTemplate.get_by_id_and_check(template_id)

        # Query all task templates for this project template and get distinct roles
        roles = (TaskTemplate
                 .select(TaskTemplate.assign_to_role)
                 .where(
                     (TaskTemplate.project_template == template_id) &
                     (TaskTemplate.assign_to_role.is_null(False))
                 )
                 .distinct()
                 .order_by(TaskTemplate.assign_to_role))

        # Extract role values and return as a list
        return [role.assign_to_role for role in roles]
