from datetime import timedelta

from gws_core import (
    BadRequestException,
    CurrentUserService,
    RichText,
    RichTextDTO,
    SpaceGroupDTO,
    SpaceGroupType,
    SpaceService,
)

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.document.document_service import DocumentService
from gws_project.document.project_document import ProjectDocument
from gws_project.project.project import Project
from gws_project.project.project_count_dto import ChildrenCountDTO, ProjectCountDTO
from gws_project.project.project_dto import (
    CreateProjectFromTemplateDTO,
    ProjectStatus,
    ProjectUserRole,
    ProjectWithRootTasksDTO,
    SaveProjectDTO,
)
from gws_project.project.project_search_builder import ProjectSearchBuilder
from gws_project.project.project_security_service import ProjectSecurityService
from gws_project.project.project_user import ProjectUser
from gws_project.task.task import Task
from gws_project.task.task_service import TaskService
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.task_template import TaskTemplate
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user import User


class ProjectService:
    """Service class for managing projects.

    Projects, tasks, documents and membership are stored locally (brick DB +
    dedicated lab file store). Space is only used as the user/group directory:
    when adding a group to a project, its users are resolved via Space and
    imported into the lab.

    :param space_service: Optional SpaceService instance to use for group/user resolution.
                         If not provided, a default SpaceService instance will be created.
    :type space_service: Optional[SpaceService]
    """

    _space_service: SpaceService

    def __init__(self, space_service: SpaceService | None = None):
        """Initialize the ProjectService with an optional SpaceService instance.

        :param space_service: Optional SpaceService instance to use for group/user resolution
        :type space_service: Optional[SpaceService]
        """
        # we use the SpaceService with token mode because this app is used within the space so the user might not be in the lab
        self._space_service = (
            space_service if space_service is not None else SpaceService("gws-project")
        )

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
            Project.select()
            .join(ProjectUser)
            .where(ProjectUser.user == current_user.id)
            .order_by(Project.title)
        )

    def count_current_user_projects(self) -> ProjectCountDTO:
        """Count all projects for the current user, grouped by status.

        :return: ProjectCountDTO with total, ongoing, done, and todo counts
        :rtype: ProjectCountDTO
        """
        projects = self.get_current_user_projects()

        ongoing = 0
        done = 0
        todo = 0
        for project in projects:
            status = project.get_status()
            if status == ProjectStatus.COMPLETED:
                done += 1
            elif status == ProjectStatus.ACTIVE:
                ongoing += 1
            else:
                todo += 1

        return ProjectCountDTO(
            total=len(projects),
            ongoing=ongoing,
            done=done,
            todo=todo,
        )

    def get_project_children_count(self, project_id: str) -> ChildrenCountDTO:
        """Get the number of direct root tasks and documents for a project.

        :param project_id: The ID of the project
        :type project_id: str
        :return: ChildrenCountDTO with subtask_count and document_count
        :rtype: ChildrenCountDTO
        """
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        # Count direct root tasks (not recursive)
        subtask_count = Task.select().where(
            (Task.project == project.id) & (Task.parent_task.is_null())
        ).count()

        # Count documents (files and notes) attached directly to the project
        document_count = ProjectDocument.count_project_documents(project.id)

        return ChildrenCountDTO(
            subtask_count=subtask_count,
            document_count=document_count,
        )

    def search_current_user_projects_with_root_tasks(
        self,
        search_title: str | None = None,
        manager_id: str | None = None,
    ) -> list[ProjectWithRootTasksDTO]:
        """Get all projects that the current user is a member of, along with their root tasks.

        This method is optimized for GANTT chart display, returning projects with their
        root-level tasks only (no subtasks). Tasks are ordered by start date.

        :return: List of ProjectWithRootTasksDTO containing projects and their root tasks
        :rtype: List[ProjectWithRootTasksDTO]
        """
        # Build the search with filters
        search_builder = ProjectSearchBuilder()

        # Filter by user's projects (projects where user is a member)
        current_user = CurrentUserService.get_and_check_current_user()
        search_builder.add_project_user_filter(current_user.id)

        # Text search filter
        if search_title:
            search_builder.add_text_search(search_title)

        # Project manager filter
        if manager_id:
            search_builder.add_project_manager_filter(manager_id)

        projects = search_builder.search_all()

        result = []
        for project in projects:
            # Get root tasks for this project (tasks without parent_task)
            root_tasks = Task.get_root_tasks_of_project(project.id)

            # Convert tasks to DTOs
            root_tasks_dtos = [task.to_dto() for task in root_tasks]

            # Create the combined DTO
            project_with_tasks = ProjectWithRootTasksDTO(
                project=project.to_dto(), root_tasks=root_tasks_dtos
            )
            result.append(project_with_tasks)

        return result

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
        """Create a project.
        Automatically adds the current user as the owner of the project.

        :param project_dto: The project data to create
        :type project_dto: SaveProjectDTO
        :return: The created project
        :rtype: Project
        """
        # Get the current user
        current_user = CurrentUserService.get_and_check_current_user()

        # Validate project dates
        self._validate_project_dates(project_dto.start_date, project_dto.end_date)

        # Create the project model from DTO
        project_manager = (
            User.get_by_id_and_check(project_dto.project_manager_id)
            if project_dto.project_manager_id
            else current_user
        )
        project = Project()
        project.title = project_dto.name
        project.description = (
            project_dto.description or RichText().to_dto()
        )  # Initialize with empty rich text
        project.start_date = project_dto.start_date
        project.end_date = project_dto.end_date
        project.project_manager = project_manager

        # Save the project model to the database
        project.save()

        # Add the current user as the owner of the project
        project_user = ProjectUser()
        project_user.project = project
        project_user.user = User.get_by_id_and_check(current_user.id)
        project_user.role = ProjectUserRole.OWNER
        project_user.save()

        return project

    @ProjectDbManager.transaction()
    def update_project(self, project_id: str, project_dto: SaveProjectDTO) -> Project:
        """Update a project.

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

        # Update the project fields from DTO
        project.title = project_dto.name
        project.start_date = project_dto.start_date
        project.end_date = project_dto.end_date
        if project_dto.project_manager_id:
            # Verify that the user is in the project
            project_user = ProjectUser.get_by_project_and_user(
                project.id, project_dto.project_manager_id
            )

            if not project_user:
                raise BadRequestException("The new project manager is not a member of the project.")

            project.project_manager = User.get_by_id_and_check(project_dto.project_manager_id)

        # Save the project model to the database
        project.save()

        return project

    @ProjectDbManager.transaction()
    def delete_project(self, project_id: str) -> None:
        """Delete a project along with its documents (hard delete, the
        documents and their files cannot be recovered).

        :param project_id: The ID of the project to delete
        :type project_id: str
        """
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.OWNER)

        # Delete the documents (and their files in the store) of the project
        # and all its tasks. The DB CASCADE would remove the rows but not the
        # file nodes on disk.
        DocumentService().delete_documents_of_project(project)

        # Delete the project from the database
        project.delete_instance()

    @ProjectDbManager.transaction()
    def add_group_to_project(
        self, project_id: str, group: SpaceGroupDTO, role: ProjectUserRole = ProjectUserRole.USER
    ) -> list[ProjectUser]:
        """Add a Space group (single user or team) to a project.

        The group type drives how its members are resolved:

        - ``TEAM``: the team's users are resolved via Space (the user/group
          directory) with :meth:`SpaceService.get_group_users`, imported into
          the lab if needed, and stored as local ProjectUser rows.
        - ``SINGLE_USER``: the single user carried by the group is added
          directly, without any extra Space call.

        Membership is enforced locally only: nothing is shared in Space.

        :param project_id: The ID of the project
        :type project_id: str
        :param group: The Space group to add
        :type group: SpaceGroupDTO
        :param role: The role of the group users in the project (default: USER)
        :type role: ProjectUserRole
        :return: The created/updated ProjectUser entities
        :rtype: List[ProjectUser]
        """
        # Get the project
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.OWNER)

        # A single-user group carries its user directly: add it without an
        # extra Space round-trip.
        if group.type == SpaceGroupType.SINGLE_USER:
            if not group.user:
                raise BadRequestException(
                    f"Single-user group '{group.id}' has no associated user."
                )
            return [self._add_user_to_project(project, group.user.id, role)]

        # A team must be resolved via Space to get its list of users.
        group_users = self._space_service.get_group_users(group.id)

        project_users = []
        for group_user in group_users:
            project_users.append(self._add_user_to_project(project, group_user.id, role))

        return project_users

    @ProjectDbManager.transaction()
    def add_user_to_project(
        self, project_id: str, user_id: str, role: ProjectUserRole = ProjectUserRole.USER
    ) -> ProjectUser:
        """Add a single user to a project.

        The user is imported into the lab if needed (via the Space user
        directory) and stored as a local ProjectUser row with the requested role.

        :param project_id: The ID of the project
        :type project_id: str
        :param user_id: The ID of the user to add
        :type user_id: str
        :param role: The role of the user in the project (default: USER)
        :type role: ProjectUserRole
        :return: The created/updated ProjectUser entity
        :rtype: ProjectUser
        """
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.OWNER)

        return self._add_user_to_project(project, user_id, role)

    def _add_user_to_project(
        self, project: Project, user_id: str, role: ProjectUserRole
    ) -> ProjectUser:
        """Import a user into the lab if needed and add it to a project.

        :param project: The project
        :type project: Project
        :param user_id: The ID of the user to add
        :type user_id: str
        :param role: The role of the user in the project
        :type role: ProjectUserRole
        :return: The created/updated ProjectUser entity
        :rtype: ProjectUser
        """
        user_sync_service = ProjectUserSyncService()
        user = user_sync_service.get_or_import_from_space_user(user_id)

        if not user:
            raise BadRequestException(f"Error importing user '{user_id}' in lab.")

        # Create the ProjectUser entity with the requested role. The lab is
        # the authority on project roles: an existing member keeps/receives
        # the requested role.
        return ProjectUser.create_or_update(project=project, user=user, role=role)

    @ProjectDbManager.transaction()
    def remove_user_from_project(self, project_id: str, user_id: str) -> None:
        """Remove a user from a project.
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

        # Delete the ProjectUser entity
        project_user.delete_instance()

    @ProjectDbManager.transaction()
    def update_user_role(self, project_id: str, user_id: str, role: ProjectUserRole) -> ProjectUser:
        """Update a user's role in a project.

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
        project_user.role = role
        project_user.save()

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
        end_date = self._calculate_project_end_date_from_template(
            project_dto.start_date, root_task_templates
        )

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
                # Add each user to the project
                self.add_user_to_project(project.id, user_id, ProjectUserRole.USER)

        # Create TaskService instance
        task_service = TaskService()

        # Create all tasks from the template
        for root_task_template in root_task_templates:
            task_service.create_task_from_template(
                project, root_task_template, project_dto.start_date, project_dto.role_mapping
            )

        return project

    def _calculate_project_end_date_from_template(
        self, project_start_date, task_templates: list[TaskTemplate]
    ):
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
