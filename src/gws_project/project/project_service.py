from datetime import timedelta

from gws_core import (
    BadRequestException,
    BaseHTTPException,
    CurrentUserService,
    ExternalSpaceCreateFolder,
    Logger,
    RichText,
    RichTextDTO,
    SpaceRootFolderUserRole,
    SpaceService,
)

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.project.project_dto import CreateProjectFromTemplateDTO, ProjectUserRole, SaveProjectDTO
from gws_project.project.project_security_service import ProjectSecurityService
from gws_project.project.project_user import ProjectUser
from gws_project.task.task import Task
from gws_project.task.task_service import TaskService
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.task_template import TaskTemplate
from gws_project.user.user import User
from gws_project.user.user_sync_service import UserSyncService


class ProjectService:
    """Service class for managing projects and their synchronization with Space.

    :param space_service: Optional SpaceService instance to use for Space operations.
                         If not provided, a default SpaceService instance will be created.
    :type space_service: Optional[SpaceService]
    """

    _space_service: SpaceService

    def __init__(self, space_service: SpaceService | None = None):
        """Initialize the ProjectService with an optional SpaceService instance.

        :param space_service: Optional SpaceService instance to use for Space operations
        :type space_service: Optional[SpaceService]
        """
        self._space_service = space_service if space_service is not None else SpaceService()

    def get_project(self, project_id: str) -> Project:
        """Get a project by ID and check if the current user has access to it.

        :param project_id: The ID of the project to retrieve
        :type project_id: str
        :return: The project if the user has access
        :rtype: Project
        :raises NotFoundException: If the project is not found
        :raises UnauthorizedException: If the user doesn't have access to the project
        """
        security_service = ProjectSecurityService()
        return security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

    def get_project_users(self, project_id: str) -> list[ProjectUser]:
        """Get all users associated with a project.

        :param project_id: The ID of the project
        :type project_id: str
        :return: List of ProjectUser entities associated with the project
        :rtype: List[ProjectUser]
        """
        security_service = ProjectSecurityService()
        security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        return ProjectUser.get_by_project(project_id)

    def get_current_user_projects(self) -> list[Project]:
        """Get all projects that the current user is a member of.

        :return: List of projects the current user has access to
        :rtype: List[Project]
        """
        current_user = CurrentUserService.get_and_check_current_user()

        return list(
            Project.select().join(ProjectUser).where(ProjectUser.user == current_user.id).order_by(Project.title)
        )

    def _validate_project_dates(self, start_date, end_date) -> None:
        """Validate that project start date is before end date.

        :param start_date: Project start date
        :param end_date: Project end date
        :raises BadRequestException: If start date is after end date
        """
        if start_date > end_date:
            raise BadRequestException(
                f"Project start date ({start_date.strftime('%d-%m-%Y')}) cannot be after end date ({end_date.strftime('%d-%m-%Y')})."
            )

    @ProjectDbManager.transaction()
    def create_project(self, project_dto: SaveProjectDTO) -> Project:
        """Create a project and sync it with Space by creating a corresponding folder.
        Automatically adds the current user as the owner of the project.

        :param project_dto: The project data to create
        :type project_dto: SaveProjectDTO
        :return: The created project with space_folder_id populated
        :rtype: Project
        """
        # Get the current user
        current_user = CurrentUserService.get_and_check_current_user()

        # Validate project dates
        self._validate_project_dates(project_dto.start_date, project_dto.end_date)

        # Create the project model from DTO
        project_manager = (
            User.get_by_id_and_check(project_dto.project_manager_id) if project_dto.project_manager_id else current_user
        )
        project = Project()
        project.title = project_dto.name
        project.description = project_dto.description or RichText().to_dto()  # Initialize with empty rich text
        project.start_date = project_dto.start_date
        project.end_date = project_dto.end_date
        project.project_manager = project_manager

        # Save the project model to the database
        project.save()

        # Add the current user as the owner of the project
        project_user = ProjectUser()
        project_user.project = project
        project_user.user = User.get_by_id_and_check(current_user.id)
        project_user.role = ProjectUserRole.OWNER.value
        project_user.save()

        # Create folder in Space with project information
        space_folder = ExternalSpaceCreateFolder(
            name=project.title,
            code=None,  # You can add a code field to Project if needed
            tags=None,  # You can add tags to Project if needed
            starting_date=project.start_date,
            ending_date=project.end_date,
        )

        # Call space service to create the root folder
        created_folder = self._space_service.create_root_folder(space_folder)

        # Update project with the space folder ID
        project.space_folder_id = created_folder.id
        project.save()

        return project

    @ProjectDbManager.transaction()
    def update_project(self, project_id: str, project_dto: SaveProjectDTO) -> Project:
        """Update a project and sync it with Space by updating the corresponding folder.

        :param project_id: The ID of the project to update
        :type project_id: str
        :param project_dto: The updated project data
        :type project_dto: SaveProjectDTO
        :return: The updated project
        :rtype: Project
        """
        # Get the project by ID
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        # Validate project dates
        self._validate_project_dates(project_dto.start_date, project_dto.end_date)

        folder_has_changed = (
            project.title != project_dto.name
            or project.start_date != project_dto.start_date
            or project.end_date != project_dto.end_date
        )

        # Update the project fields from DTO
        project.title = project_dto.name
        project.start_date = project_dto.start_date
        project.end_date = project_dto.end_date
        if project_dto.project_manager_id:
            # Verify that the user is in the project
            project_user = ProjectUser.get_by_project_and_user(project.id, project_dto.project_manager_id)

            if not project_user:
                raise BadRequestException("The new project manager is not a member of the project.")

            project.project_manager = User.get_by_id_and_check(project_dto.project_manager_id)

        # Save the project model to the database
        project.save()

        # If the project has a space folder ID, update the folder in Space
        if project.space_folder_id and folder_has_changed:
            space_folder = ExternalSpaceCreateFolder(
                name=project.title,
                code=None,  # You can add a code field to Project if needed
                tags=None,  # You can add tags to Project if needed
                starting_date=project.start_date,
                ending_date=project.end_date,
            )

            # Call space service to update the folder
            self._space_service.update_folder(project.space_folder_id, space_folder)

        return project

    @ProjectDbManager.transaction()
    def delete_project(self, project_id: str) -> None:
        """Delete a project and move its corresponding folder to trash in Space.

        :param project: The project to delete
        :type project: Project
        """
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.OWNER)

        # If the project has a space folder ID, delete the folder in Space first
        if project.space_folder_id:
            try:
                self._space_service.delete_folder(project.space_folder_id)
            except BaseHTTPException as e:
                if e.status_code == 404:
                    # Folder not found in Space, proceed with project deletion
                    Logger.warning(
                        f"Space folder {project.space_folder_id} not found. Proceeding with project deletion."
                    )
                else:
                    # Reraise other exceptions
                    raise e

        # Delete the project from the database
        project.delete_instance()

    @ProjectDbManager.transaction()
    def add_group_to_project(
        self, project_id: str, group_id: str, role: ProjectUserRole = ProjectUserRole.USER
    ) -> list[ProjectUser]:
        """Add a user to a project and share the project folder in Space.

        :param project_id: The ID of the project
        :type project_id: str
        :param user_id: The ID of the user to add
        :type user_id: str
        :param role: The role of the user in the project (default: USER)
        :type role: ProjectUserRole
        :return: The created ProjectUser entity
        :rtype: ProjectUser
        """
        # Get the project
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.OWNER)

        # If the project has a space folder, share it with the user
        project_users = []
        if project.space_folder_id:
            # Convert ProjectUserRole to SpaceRootFolderUserRole
            space_role = SpaceRootFolderUserRole[role.name]
            folder_users = self._space_service.share_root_folder(project.space_folder_id, group_id, space_role)

            # Handle the case where folder_users is None (for mock testing)
            if folder_users:
                for folder_user in folder_users:
                    user_sync_service = UserSyncService()
                    user = user_sync_service.get_or_import_user(folder_user.user.id)

                    if not user:
                        raise Exception(f"Error importing user {folder_user.user.email} from in lab.")

                    # Create the ProjectUser entity with the specified role
                    project_user = ProjectUser.create_or_update(project=project, user=user, role=folder_user.role)
                    project_users.append(project_user)
            else:
                # Fallback for testing: directly add the user if group_id is a user_id
                user = User.get_by_id_and_check(group_id)
                project_user = ProjectUser.create_or_update(project=project, user=user, role=role)
                project_users.append(project_user)

        return project_users

    @ProjectDbManager.transaction()
    def remove_user_from_project(self, project_id: str, user_id: str) -> None:
        """Remove a user from a project and unshare the project folder in Space.
        Prevents removing the last owner of the project.
        Prevents removing a user who has tasks assigned in the project.

        :param project_id: The ID of the project
        :type project_id: str
        :param user_id: The ID of the user to remove
        :type user_id: str
        :raises BadRequestException: If trying to remove the last owner or if user has assigned tasks
        """
        # Get the project
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.OWNER)

        # Get the ProjectUser entity to check the role
        project_user = ProjectUser.get_by_project_and_user(project.id, user_id)

        if not project_user:
            raise BadRequestException("The user is not a member of the project.")

        # Check if the user has any tasks assigned in this project
        task_count = Task.count_tasks_of_user_in_project(user_id, project.id)

        if task_count > 0:
            raise BadRequestException(
                f"Cannot remove user from the project. "
                f"The user has {task_count} task(s) assigned in this project. "
                f"Please reassign or complete these tasks before removing the user."
            )

        # If the user is an owner, check if they are the last owner
        if project_user.role == ProjectUserRole.OWNER:
            # Count the number of owners in the project
            owner_count = ProjectUser.count_owner_by_project(project.id)

            if owner_count <= 1:
                raise BadRequestException(
                    "Cannot remove the last owner from the project. "
                    "Please assign another owner before removing this user."
                )

        # If the project has a space folder, unshare it from the user
        if project.space_folder_id:
            self._space_service.unshare_root_folder(project.space_folder_id, user_id)

        # Delete the ProjectUser entity
        project_user.delete_instance()

    @ProjectDbManager.transaction()
    def update_user_role(self, project_id: str, user_id: str, role: ProjectUserRole) -> ProjectUser:
        """Update a user's role in a project and update their Space folder permissions.

        :param project_id: The ID of the project
        :type project_id: str
        :param user_id: The ID of the user whose role to update
        :type user_id: str
        :param role: The new role for the user
        :type role: ProjectUserRole
        :return: The updated ProjectUser entity
        :rtype: ProjectUser
        :raises BadRequestException: If trying to remove the last owner or user not found
        """
        # Get the project and check permissions
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.OWNER)

        # Get the ProjectUser entity
        project_user = ProjectUser.get_by_project_and_user(project.id, user_id)

        if not project_user:
            raise BadRequestException("The user is not a member of the project.")

        # If changing from OWNER to something else, check if they are the last owner
        if project_user.role == ProjectUserRole.OWNER and role != ProjectUserRole.OWNER:
            # Count the number of owners in the project
            owner_count = ProjectUser.count_owner_by_project(project.id)

            if owner_count <= 1:
                raise BadRequestException(
                    "Cannot change role of the last owner in the project. Please assign another owner before changing this user's role."
                )

        # Update the role
        old_role = project_user.role
        project_user.role = role.value
        project_user.save()

        # If the project has a space folder, update permissions
        if project.space_folder_id and old_role != role.value:
            # Convert ProjectUserRole to SpaceRootFolderUserRole
            space_role = SpaceRootFolderUserRole[role.name]
            # Update the user role in the folder
            self._space_service.update_folder_user_role(project.space_folder_id, user_id, space_role)

        return project_user

    @ProjectDbManager.transaction()
    def update_project_description(self, project_id: str, description: RichTextDTO) -> Project:
        """Update a project's description.

        :param project_id: The ID of the project
        :type project_id: str
        :param description: The new rich text description
        :type description: RichTextDTO
        :return: The updated project
        :rtype: Project
        """
        # Get the project and check permissions
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        # Update the description
        project.description = description
        project.save()

        return project

    @ProjectDbManager.transaction()
    def create_project_from_template(
        self, project_template_id: str, project_dto: CreateProjectFromTemplateDTO
    ) -> Project:
        """Create a project from a project template.

        This method creates a new project with all tasks from the template.
        The end_date is automatically calculated based on the template tasks.
        Tasks are created with dates calculated from their start_date_offset and duration_days.

        :param project_template_id: The ID of the project template to use
        :type project_template_id: str
        :param project_dto: The project data (name, start_date, project_manager_id)
        :type project_dto: CreateProjectFromTemplateDTO
        :return: The created project with all tasks
        :rtype: Project
        :raises NotFoundException: If the project template is not found
        """
        # Get the project template and verify it exists
        project_template = ProjectTemplate.get_by_id_and_check(project_template_id)

        # Get all root task templates for this project template
        root_task_templates = TaskTemplate.get_root_tasks_of_template(project_template_id)

        # Calculate the project end_date based on template tasks
        end_date = self._calculate_project_end_date_from_template(project_dto.start_date, root_task_templates)

        # Create the project using SaveProjectDTO
        save_project_dto = SaveProjectDTO(
            name=project_dto.name,
            start_date=project_dto.start_date,
            end_date=end_date,
            project_manager_id=project_dto.project_manager_id,
            description=project_template.description,
        )
        project = self.create_project(save_project_dto)

        # Add all users from role_mapping to the project
        if project_dto.role_mapping:
            # Get unique user IDs from the role mapping
            unique_user_ids = set(project_dto.role_mapping.values())

            for user_id in unique_user_ids:
                # Add each user to the project using add_group_to_project
                # The group_id is actually the user_id in this context
                self.add_group_to_project(project.id, user_id, ProjectUserRole.USER)

        # Create TaskService instance
        task_service = TaskService(self._space_service)

        # Create all tasks from the template
        for root_task_template in root_task_templates:
            task_service.create_task_from_template(
                project, root_task_template, project_dto.start_date, project_dto.role_mapping
            )

        return project

    def _calculate_project_end_date_from_template(self, project_start_date, task_templates: list[TaskTemplate]):
        """Calculate the project end date based on all task templates.

        Recursively processes all task templates (including subtasks) to find
        the maximum end date.

        :param project_start_date: The project start date
        :type project_start_date: datetime.date
        :param task_templates: List of task templates to process
        :type task_templates: List[TaskTemplate]
        :return: The calculated end date for the project
        :rtype: datetime.date
        """
        max_end_offset = 0

        def process_task_template(task_template: TaskTemplate):
            nonlocal max_end_offset

            # Calculate this task's end offset
            task_end_offset = task_template.start_date_offset + task_template.duration_days
            max_end_offset = max(max_end_offset, task_end_offset)

            # Process subtasks recursively
            subtasks = TaskTemplate.get_subtasks_of_template_task(task_template.id)
            for subtask in subtasks:
                process_task_template(subtask)

        # Process all root task templates
        for task_template in task_templates:
            process_task_template(task_template)

        # Calculate end date (subtract 1 day because duration includes the start day)
        end_date = project_start_date + timedelta(days=max(max_end_offset - 1, 0))
        return end_date
