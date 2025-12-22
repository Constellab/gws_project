


from gws_core import BadRequestException, RichText, RichTextDTO

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_dto import SaveTaskTemplateDTO, UpdateTaskTemplateDTO


class TaskTemplateService:
    """Service class for managing task templates.

    This service provides methods to create, update, delete, and query task templates
    that are part of project templates.
    """

    def get_task_template(self, task_template_id: str) -> TaskTemplate:
        """Get a task template by ID.

        :param task_template_id: The ID of the task template to retrieve
        :type task_template_id: str
        :return: The task template
        :rtype: TaskTemplate
        :raises NotFoundException: If the task template is not found
        """
        return TaskTemplate.get_by_id_and_check(task_template_id)

    def get_root_tasks_of_template(self, template_id: str) -> list[TaskTemplate]:
        """Get all root task templates for a project template.

        :param template_id: The ID of the project template
        :type template_id: str
        :return: List of root task templates ordered by created_at
        :rtype: List[TaskTemplate]
        """
        return TaskTemplate.get_root_tasks_of_template(template_id)

    def get_subtasks_of_task_template(self, task_template_id: str) -> list[TaskTemplate]:
        """Get all subtasks for a task template.

        :param task_template_id: The ID of the task template
        :type task_template_id: str
        :return: List of subtask templates ordered by created_at
        :rtype: List[TaskTemplate]
        :raises NotFoundException: If the task template is not found
        """
        # Verify task template exists
        TaskTemplate.get_by_id_and_check(task_template_id)

        return TaskTemplate.get_subtasks_of_template_task(task_template_id)

    @ProjectDbManager.transaction()
    def create_task_template(self, template_id: str, task_template_dto: SaveTaskTemplateDTO,
                             parent_task_id: str = None) -> TaskTemplate:
        """Create a new task template for a project template.

        Supports unlimited nesting levels - task templates can be created under any task template
        that allows subtasks, enabling hierarchies of arbitrary depth.

        :param template_id: The ID of the project template
        :type template_id: str
        :param task_template_dto: The task template data to create
        :type task_template_dto: CreateTaskTemplateDTO
        :param parent_task_id: Optional parent task template ID for creating subtasks at any level
        :type parent_task_id: str
        :return: The created task template
        :rtype: TaskTemplate
        :raises NotFoundException: If the template or parent task is not found
        :raises BadRequestException: If validation fails or parent doesn't allow subtasks
        """

        # Verify the project template exists
        project_template = ProjectTemplate.get_by_id_and_check(template_id)

        # If parent_task_id is provided, verify it exists and belongs to the same template
        parent_task = None
        if parent_task_id:
            parent_task = TaskTemplate.get_by_id_and_check(parent_task_id)

            # Verify parent task belongs to the same template
            if parent_task.project_template.id != template_id:
                raise BadRequestException(
                    "Parent task template does not belong to the specified project template."
                )

            # Verify parent task allows subtasks (supports unlimited nesting)
            if not parent_task.allow_subtasks:
                raise BadRequestException(
                    "Parent task template does not allow subtasks."
                )

        # Validate dates
        if task_template_dto.start_date_offset < 0:
            raise BadRequestException(
                "Start date offset cannot be negative."
            )

        if task_template_dto.duration_days <= 0:
            raise BadRequestException(
                "Task duration must be at least 1 day."
            )

        # Create the task template
        task_template = TaskTemplate()
        task_template.project_template = project_template
        task_template.parent_task = parent_task
        task_template.title = task_template_dto.title
        task_template.description = RichText().to_dto()  # Initialize with empty rich text
        task_template.start_date_offset = task_template_dto.start_date_offset
        task_template.duration_days = task_template_dto.duration_days
        task_template.priority = task_template_dto.priority
        task_template.allow_subtasks = task_template_dto.allow_subtasks
        task_template.assign_to_role = task_template_dto.assign_to_role

        # Save to database
        task_template.save()

        return task_template

    @ProjectDbManager.transaction()
    def update_task_template(self, task_template_id: str,
                             task_template_dto: UpdateTaskTemplateDTO) -> TaskTemplate:
        """Update an existing task template.

        :param task_template_id: The ID of the task template to update
        :type task_template_id: str
        :param task_template_dto: The updated task template data
        :type task_template_dto: UpdateTaskTemplateDTO
        :return: The updated task template
        :rtype: TaskTemplate
        :raises NotFoundException: If the task template is not found
        :raises BadRequestException: If validation fails
        """
        # Get the task template
        task_template = TaskTemplate.get_by_id_and_check(task_template_id)

        # Validate dates
        if task_template_dto.start_date_offset < 0:
            raise BadRequestException(
                "Start date offset cannot be negative."
            )

        if task_template_dto.duration_days <= 0:
            raise BadRequestException(
                "Task duration must be at least 1 day."
            )

        # Update the task template fields
        task_template.title = task_template_dto.title
        task_template.start_date_offset = task_template_dto.start_date_offset
        task_template.duration_days = task_template_dto.duration_days
        task_template.priority = task_template_dto.priority
        task_template.assign_to_role = task_template_dto.assign_to_role

        # Save to database
        task_template.save()

        return task_template

    @ProjectDbManager.transaction()
    def delete_task_template(self, task_template_id: str) -> None:
        """Delete a task template and all its descendants recursively.

        For task templates with subtasks: Deletes all descendants at all levels (children, grandchildren, etc.)
        The cascade delete will automatically remove all descendants through the database foreign key.

        :param task_template_id: The ID of the task template to delete
        :type task_template_id: str
        :raises NotFoundException: If the task template is not found
        """
        # Get the task template
        task_template = TaskTemplate.get_by_id_and_check(task_template_id)

        # Delete the task template
        # Database CASCADE on the foreign key will handle recursive deletion of all descendants
        task_template.delete_instance()

    @ProjectDbManager.transaction()
    def update_task_template_description(self, task_template_id: str,
                                         description: RichTextDTO) -> TaskTemplate:
        """Update a task template's description.

        :param task_template_id: The ID of the task template
        :type task_template_id: str
        :param description: The new rich text description
        :type description: RichTextDTO
        :return: The updated task template
        :rtype: TaskTemplate
        """
        # Get the task template
        task_template = TaskTemplate.get_by_id_and_check(task_template_id)

        # Update the description
        task_template.description = description
        task_template.save()

        return task_template

    @ProjectDbManager.transaction()
    def update_priority(self, task_template_id: str, priority: str) -> TaskTemplate:
        """Update a task template's priority.

        :param task_template_id: The ID of the task template
        :type task_template_id: str
        :param priority: The new priority value
        :type priority: str
        :return: The updated task template
        :rtype: TaskTemplate
        :raises NotFoundException: If the task template is not found
        """
        # Get the task template
        task_template = TaskTemplate.get_by_id_and_check(task_template_id)

        # Update the priority
        task_template.priority = priority
        task_template.save()

        return task_template
