
from datetime import date, timedelta
from typing import Dict, List, Optional

from gws_core import (BadRequestException, BaseHTTPException,
                      CurrentUserService, ExternalSpaceCreateFolder, Logger,
                      RichText, RichTextDTO, SearchParams, SpaceService)
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.project.project_security_service import (
    ProjectSecurityService, ProjectUserRole)
from gws_project.project.project_user import ProjectUser
from gws_project.task.task import Task
from gws_project.task.task_dto import (CreateTaskDTO, TaskPriority, TaskStatus,
                                       UpdateTaskDTO)
from gws_project.task.task_search_builder import TaskSearchBuilder
from gws_project.template.task_template import TaskTemplate
from gws_project.user.user import User


class TaskService:
    """Service class for managing tasks and their synchronization with Space.

    :param space_service: Optional SpaceService instance to use for Space operations.
                         If not provided, a default SpaceService instance will be created.
    :type space_service: Optional[SpaceService]
    """

    def __init__(self, space_service: Optional[SpaceService] = None):
        """Initialize the TaskService with an optional SpaceService instance.

        :param space_service: Optional SpaceService instance to use for Space operations
        :type space_service: Optional[SpaceService]
        """
        self._space_service = space_service if space_service is not None else SpaceService()

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID and check if the current user has access to it.

        :param task_id: The ID of the task to retrieve
        :type task_id: str
        :return: The task if the user has access
        :rtype: Task
        :raises NotFoundException: If the task is not found
        :raises UnauthorizedException: If the user doesn't have access to the task
        """
        security_service = ProjectSecurityService()
        return security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

    def get_root_tasks_of_project(self, project_id: str) -> List[Task]:
        """Get the root task of a project by project ID.

        :param project_id: The ID of the project
        :type project_id: str
        :return: The root tasks if the user has access
        :rtype: List[Task]
        :raises NotFoundException: If the project is not found
        :raises UnauthorizedException: If the user doesn't have access to the project
        """
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        return Task.get_root_tasks_of_project(project)

    def get_subtasks(self, parent_task_id: str) -> List[Task]:
        """Get all subtasks of a parent task by parent task ID.

        :param parent_task_id: The ID of the parent task
        :type parent_task_id: str
        :return: List of subtasks if the user has access
        :rtype: List[Task]
        :raises NotFoundException: If the parent task is not found
        :raises UnauthorizedException: If the user doesn't have access to the parent task
        """
        security_service = ProjectSecurityService()
        parent_task = security_service.get_and_check_role_for_task(parent_task_id, ProjectUserRole.USER)

        return Task.get_subtasks_of_task(parent_task.id)

    def search(self, search: SearchParams = None) -> List[Task]:
        """Search for tasks based on search parameters with pagination.

        :param search: The search parameters
        :type search: SearchParams
        :param page: The page number (0-indexed)
        :type page: int
        :param number_of_items_per_page: Number of items per page
        :type number_of_items_per_page: int
        :return: A paginator containing the search results
        :rtype: Paginator[Task]
        """
        user_projects = ProjectUser.get_projects_of_user(CurrentUserService.get_and_check_current_user().id)

        project_ids = [project.id for project in user_projects]

        search_builder = TaskSearchBuilder()
        search_builder.add_projects_filter(project_ids)

        if search:
            search_builder.add_search_params(search)
        return search_builder.search_all()

    @ProjectDbManager.transaction()
    def create_root_task(self, project_id: str, task_dto: CreateTaskDTO) -> Task:
        """Create a root task (task without parent) and sync it with Space by creating a child folder.

        :param project_id: The ID of the project
        :type project_id: str
        :param task_dto: The task data to create
        :type task_dto: CreateTaskDTO
        :return: The created task with space_folder_id populated
        :rtype: Task
        :raises BadRequestException: If dates are outside project bounds or user is not in project
        """
        # Get the project and ensure it exists
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        # Validate task dates are within project dates
        start_date = task_dto.start_date or project.start_date
        end_date = task_dto.end_date or project.end_date
        self._validate_task_dates_within_project(project, start_date, end_date)

        # Create the task model from DTO using common method
        task = self._build_task_from_dto(task_dto, project, parent_task=None)

        # Save the task to the database
        task.save()

        # Create a child folder in Space if the project has a space folder
        if project.space_folder_id:
            space_folder = ExternalSpaceCreateFolder(
                name=task.title,
                code=None,
                tags=None,
                starting_date=task.start_date,
                ending_date=task.end_date
            )

            # Call space service to create the child folder
            created_folder = self._space_service.create_child_folder(project.space_folder_id, space_folder)

            # Update task with the space folder ID
            task.space_folder_id = created_folder.id
            task.save()

        return task

    @ProjectDbManager.transaction()
    def create_sub_task(self, parent_task_id: str, task_dto: CreateTaskDTO) -> Task:
        """Create a subtask under a parent task. Does not create a folder in Space.
        Only allows creating subtasks under root tasks (no nested subtasks).
        Parent task dates, status, and priority are automatically updated based on all subtasks.

        :param parent_task_id: The ID of the parent task
        :type parent_task_id: str
        :param task_dto: The subtask data to create
        :type task_dto: CreateTaskDTO
        :return: The created subtask
        :rtype: Task
        :raises BadRequestException: If parent task doesn't allow subtasks, is not a root task,
                                      or user is not in project
        """
        # Get the parent task and ensure it exists
        security_service = ProjectSecurityService()
        parent_task = security_service.get_and_check_role_for_task(parent_task_id, ProjectUserRole.USER)

        # Check that the parent task allows subtasks
        if not parent_task.allow_subtasks:
            raise BadRequestException(
                "Cannot create subtask. The parent task does not allow subtasks. "
                "Set 'allow_subtasks' to true on the parent task."
            )

        # Check that the parent task is a root task (no nested subtasks allowed)
        if not parent_task.is_root_task():
            raise BadRequestException(
                "Cannot create subtask. Nested subtasks are not allowed. "
                "Subtasks can only be created under root tasks (tasks without a parent)."
            )

        # Create the subtask model from DTO using common method
        # Force allow_subtasks to False and use project dates as defaults
        subtask = self._build_task_from_dto(
            task_dto,
            parent_task.project,
            parent_task=parent_task,
            force_allow_subtasks=False
        )

        # Use the parent space folder id
        subtask.space_folder_id = parent_task.space_folder_id

        # Save the subtask to the database
        subtask.save()

        # Update parent task information based on all subtasks (including the new one)
        self._update_parent_task_from_subtasks(parent_task)

        # Note: We do NOT create a folder in Space for subtasks

        return subtask

    @ProjectDbManager.transaction()
    def update_task(self, task_id: str, task_dto: UpdateTaskDTO) -> Task:
        """Update a task.

        For subtasks: Updates title, description, dates, and priority, then recalculates parent task info.
        For parent tasks: Only updates title and description. Dates, status, and priority are
                         automatically calculated from subtasks.
        For root tasks without subtasks: Updates all fields and syncs with Space folder.

        :param task_id: The ID of the task to update
        :type task_id: str
        :param task_dto: The updated task data
        :type task_dto: UpdateTaskDTO
        :return: The updated task
        :rtype: Task
        :raises BadRequestException: If task is a parent task and trying to update dates/priority,
                                      or if dates are outside valid bounds
        """
        # Get the task and ensure it exists
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Check if this task has subtasks (is a parent task)
        if task.allow_subtasks:
            # For parent tasks, only allow updating title
            # Dates, status, and priority are calculated from subtasks
            task.title = task_dto.title
            task.save()

            # Recalculate parent task information from subtasks
            self._update_parent_task_from_subtasks(task)

            return task

        # For tasks without subtasks (regular tasks or subtasks)

        # Check if title or dates have changed
        folder_has_changed = task.title != task_dto.title or \
            task.start_date != task_dto.start_date or \
            task.end_date != task_dto.end_date

        # Validate dates based on whether this is a root task or subtask
        if task.is_root_task():
            # For root tasks, validate against project dates
            self._validate_task_dates_within_project(task.project, task_dto.start_date, task_dto.end_date)
        else:
            # For subtasks, dates are no longer validated against parent since parent adjusts automatically
            # Just validate that start_date <= end_date
            if task_dto.start_date > task_dto.end_date:
                raise BadRequestException(
                    f"Task start date ({task_dto.start_date}) cannot be after its end date ({task_dto.end_date})."
                )

        # Update the task fields from DTO
        task.title = task_dto.title
        if task_dto.start_date:
            task.start_date = task_dto.start_date
        if task_dto.end_date:
            task.end_date = task_dto.end_date
        if task_dto.status:
            task.status = task_dto.status
        if task_dto.priority:
            task.priority = task_dto.priority

        # Save the task to the database
        task.save()

        # If this is a subtask, update the parent task information
        if not task.is_root_task():
            self._update_parent_task_from_subtasks(task.parent_task)

        # If this is a root task with a space folder, update the folder in Space
        if task.is_root_task() and task.space_folder_id and folder_has_changed:
            space_folder = ExternalSpaceCreateFolder(
                name=task.title,
                code=None,
                tags=None,
                starting_date=task.start_date,
                ending_date=task.end_date
            )

            # Call space service to update the folder
            self._space_service.update_folder(task.space_folder_id, space_folder)

        return task

    @ProjectDbManager.transaction()
    def update_assign_to(self, task_id: str, user_id: str) -> Task:
        """Update the assignment of a task to a new user.

        :param task_id: The ID of the task to update
        :type task_id: str
        :param user_id: The ID of the user to assign the task to
        :type user_id: str
        :return: The updated task
        :rtype: Task
        :raises BadRequestException: If user is not a member of the project
        """
        # Get the task and ensure it exists
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Update the task assignment
        task.assign_to = self._validate_assign_to_in_project(task.project.id, user_id)

        # Save the task to the database
        task.save()

        return task

    @ProjectDbManager.transaction()
    def update_status(self, task_id: str, status: TaskStatus) -> Task:
        """Update the status of a task and automatically update parent task information if applicable.

        :param task_id: The ID of the task to update
        :type task_id: str
        :param status: The new status for the task
        :type status: TaskStatus
        :return: The updated task
        :rtype: Task
        :raises BadRequestException: If the task allows subtasks (status is calculated automatically)
        """
        # Get the task and ensure it exists
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Validate that the task does not allow subtasks
        # Tasks with subtasks have their status calculated automatically
        if task.allow_subtasks:
            raise BadRequestException(
                "Cannot manually update status for tasks with subtasks. "
                "The status is calculated automatically based on subtask statuses."
            )

        # Validate that the new status is not the same as the current status
        if task.status == status:
            return task  # No change needed

        # Update the task status
        task.status = status

        # Save the task to the database
        task.save()

        # Update parent task information if this is a subtask
        # This updates not just status, but also dates and priority based on all subtasks
        if task.parent_task:
            self._update_parent_task_from_subtasks(task.parent_task)

        return task

    @ProjectDbManager.transaction()
    def update_priority(self, task_id: str, priority: TaskPriority) -> Task:
        """Update the priority of a task and automatically update parent task information if applicable.

        :param task_id: The ID of the task to update
        :type task_id: str
        :param priority: The new priority for the task
        :type priority: TaskPriority
        :return: The updated task
        :rtype: Task
        :raises BadRequestException: If the task allows subtasks (priority is calculated automatically)
        """
        # Get the task and ensure it exists
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Validate that the task does not allow subtasks
        # Tasks with subtasks have their priority calculated automatically
        if task.allow_subtasks:
            raise BadRequestException(
                "Cannot manually update priority for tasks with subtasks. "
                "The priority is calculated automatically based on subtask priorities."
            )

        # Validate that the new priority is not the same as the current priority
        if task.priority == priority:
            return task  # No change needed

        # Update the task priority
        task.priority = priority

        # Save the task to the database
        task.save()

        # Update parent task information if this is a subtask
        # This updates not just priority, but also dates and status based on all subtasks
        if task.parent_task:
            self._update_parent_task_from_subtasks(task.parent_task)

        return task

    @ProjectDbManager.transaction()
    def delete_task(self, task_id: str) -> None:
        """Delete a task. If it's a root task, also deletes all subtasks and the Space folder.
        If it's a subtask, updates the parent task information after deletion.

        :param task_id: The ID of the task to delete
        :type task_id: str
        """
        # Get the task and ensure it exists
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Store parent task reference before deletion if this is a subtask
        parent_task = task.parent_task if not task.is_root_task() else None

        # If this is a root task with subtasks, delete all subtasks first
        if task.allow_subtasks:
            # Delete all subtasks (Peewee will handle this via CASCADE on the foreign key)
            # But we'll explicitly query and delete to be clear
            subtasks = task.get_subtasks()
            for subtask in subtasks:
                subtask.delete_instance()

        # Delete the task from the database
        task.delete_instance()

        # If this was a subtask, update the parent task information
        if parent_task:
            self._update_parent_task_from_subtasks(parent_task)

        # If this is a root task with a space folder, delete the folder in Space
        if task.is_root_task() and task.space_folder_id:
            try:
                self._space_service.delete_folder(task.space_folder_id)
            except BaseHTTPException as e:
                if e.status_code == 404:
                    # Folder not found in Space, proceed with project deletion
                    Logger.warning(
                        f"Space folder {task.space_folder_id} not found. Proceeding with project deletion.")
                else:
                    # Reraise other exceptions
                    raise e

    def _validate_task_dates_within_project(self, project: Project, task_start_date: date, task_end_date: date) -> None:
        """Validate that task dates are within project dates.

        :param project: The project
        :type project: Project
        :param task_start_date: Task start date
        :type task_start_date: date
        :param task_end_date: Task end date
        :type task_end_date: date
        :raises BadRequestException: If dates are outside project bounds
        """
        if task_start_date < project.start_date:
            raise BadRequestException(
                f"Task start date ({task_start_date}) cannot be before project start date ({project.start_date})."
            )
        if task_end_date > project.end_date:
            raise BadRequestException(
                f"Task end date ({task_end_date}) cannot be after project end date ({project.end_date})."
            )
        if task_start_date > task_end_date:
            raise BadRequestException(
                f"Task start date ({task_start_date}) cannot be after its end date ({task_end_date})."
            )

    def _validate_assign_to_in_project(self, project_id: str, user_id: str | None) -> User:
        """Validate that the user to whom the task is assigned is a member of the project.

        :param project_id: The project ID
        :type project_id: str
        :param user_id: The ID of the user to whom the task is assigned
        :type user_id: str
        :raises BadRequestException: If user is not a member of the project
        """
        if not user_id:
            # no need to check access for current user, it was already checked when getting the project
            return CurrentUserService.get_and_check_current_user()

        if not ProjectUser.is_user_in_project(project_id, user_id):
            raise BadRequestException(
                f"User with ID '{user_id}' is not a member of the project. "
                "Please add the user to the project before assigning tasks."
            )

        return User.get_by_id_and_check(user_id)

    def _build_task_from_dto(
        self,
        task_dto: CreateTaskDTO,
        project: Project,
        parent_task: Optional[Task] = None,
        force_allow_subtasks: Optional[bool] = None
    ) -> Task:
        """Build a Task model from a CreateTaskDTO.

        :param task_dto: The task data transfer object
        :type task_dto: CreateTaskDTO
        :param project: The project this task belongs to
        :type project: Project
        :param parent_task: The parent task if this is a subtask (optional)
        :type parent_task: Optional[Task]
        :param force_allow_subtasks: Force allow_subtasks to a specific value (optional)
        :type force_allow_subtasks: Optional[bool]
        :return: The created task (not yet saved to database)
        :rtype: Task
        """
        task = Task()
        task.project = project
        task.parent_task = parent_task
        task.title = task_dto.title
        task.description = RichText().to_dto()  # Initialize with empty rich text

        # Set dates with defaults from project
        task.start_date = task_dto.start_date or project.start_date
        task.end_date = task_dto.end_date or project.end_date

        # Set status and priority with defaults
        task.status = task_dto.status or TaskStatus.TODO
        task.priority = task_dto.priority or TaskPriority.MEDIUM

        # Set allow_subtasks - can be forced (for subtasks) or from DTO
        if force_allow_subtasks is not None:
            task.allow_subtasks = force_allow_subtasks
        else:
            task.allow_subtasks = task_dto.allow_subtasks

        # Validate and set assigned user
        task.assign_to = self._validate_assign_to_in_project(project.id, task_dto.assign_to_id)

        return task

    def _update_parent_task_from_subtasks(self, parent_task: Task) -> None:
        """Update parent task information (dates, status, priority) based on all its subtasks.

        This method automatically calculates:
        - Start date: earliest start date of all subtasks (or project start date if no subtasks)
        - End date: latest end date of all subtasks (or project end date if no subtasks)
        - Status: based on subtask statuses (or TODO if no subtasks)
        - Priority: highest priority among all subtasks (or MEDIUM if no subtasks)

        Only saves to database and updates Space if there were actual changes.

        :param parent_task: The parent task to update
        :type parent_task: Task
        """
        # Update from subtasks (calculates dates, status, and priority)
        has_changes = parent_task.update_from_subtasks()

        # Only save and update Space if there were changes
        if has_changes:
            # Save the updated parent task
            parent_task.save()

            # Update Space folder if this is a root task
            if parent_task.is_root_task() and parent_task.space_folder_id:
                space_folder = ExternalSpaceCreateFolder(
                    name=parent_task.title,
                    code=None,
                    tags=None,
                    starting_date=parent_task.start_date,
                    ending_date=parent_task.end_date
                )
                self._space_service.update_folder(parent_task.space_folder_id, space_folder)

    @ProjectDbManager.transaction()
    def update_task_description(self, task_id: str, description: RichTextDTO) -> Task:
        """Update a task's description.

        :param task_id: The ID of the task
        :type task_id: str
        :param description: The new rich text description
        :type description: RichTextDTO
        :return: The updated task
        :rtype: Task
        """
        # Get the task and check permissions
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Update the description
        task.description = description
        task.save()

        return task

    def get_subtask_assigned_users(self, task_id: str) -> List[User]:
        """Get the list of unique users assigned to subtasks of a task.

        Returns an empty list if the task has no subtasks or if no users are assigned.

        :param task_id: The ID of the parent task
        :type task_id: str
        :return: List of unique users assigned to the subtasks
        :rtype: List[User]
        :raises NotFoundException: If the task is not found
        :raises UnauthorizedException: If the user doesn't have access to the task
        """
        # Get the task and check permissions
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Get all subtasks of the task
        subtasks = Task.get_subtasks_of_task(task.id)

        # Extract unique users using a dictionary to preserve order and avoid duplicates
        seen_user_ids = set()
        unique_users = []

        for subtask in subtasks:
            if subtask.assign_to and subtask.assign_to.id not in seen_user_ids:
                seen_user_ids.add(subtask.assign_to.id)
                unique_users.append(subtask.assign_to)

        return unique_users

    def create_task_from_template(
        self,
        project: Project,
        task_template: TaskTemplate,
        project_start_date: date,
        role_mapping: Optional[Dict[str, str]] = None,
        parent_task: Optional[Task] = None
    ) -> Task:
        """Create a task from a task template.

        Recursively creates subtasks if the template has subtasks.

        :param project: The project to create the task in
        :type project: Project
        :param task_template: The task template to create the task from
        :type task_template: TaskTemplate
        :param project_start_date: The project start date for calculating task dates
        :type project_start_date: date
        :param role_mapping: Dictionary mapping role names to user IDs
        :type role_mapping: Optional[Dict[str, str]]
        :param parent_task: The parent task if this is a subtask
        :type parent_task: Optional[Task]
        :return: The created task
        :rtype: Task
        """
        # Calculate task dates based on template offsets
        task_start_date = project_start_date + timedelta(days=task_template.start_date_offset)
        # Subtract 1 because duration includes the start day
        task_end_date = task_start_date + timedelta(days=max(task_template.duration_days - 1, 0))

        # Determine the user to assign the task to using role mapping
        assign_to_user_id = self._get_assign_to_user_id_from_role(
            task_template.assign_to_role,
            role_mapping
        )

        # Create task DTO
        task_dto = CreateTaskDTO(
            title=task_template.title,
            start_date=task_start_date,
            end_date=task_end_date,
            status=TaskStatus.TODO,
            priority=task_template.priority,
            allow_subtasks=task_template.allow_subtasks,
            assign_to_id=assign_to_user_id
        )

        # Create the task using TaskService methods
        if parent_task is None:
            # Create root task
            task = self.create_root_task(project.id, task_dto)
        else:
            # Create subtask
            task = self.create_sub_task(parent_task.id, task_dto)

        # Copy the description from the template
        if task_template.description:
            task.description = task_template.description
            task.save()

        # Create subtasks recursively
        subtasks = TaskTemplate.get_subtasks_of_template_task(task_template.id)
        for subtask_template in subtasks:
            self.create_task_from_template(
                project,
                subtask_template,
                project_start_date,
                role_mapping,
                task
            )

        return task

    def _get_assign_to_user_id_from_role(
        self,
        assign_to_role: Optional[str],
        role_mapping: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Get the user ID to assign a task to based on the template role and role mapping.

        :param project: The project
        :type project: Project
        :param assign_to_role: The role from the template
        :type assign_to_role: Optional[str]
        :param role_mapping: Dictionary mapping role names to user IDs
        :type role_mapping: Optional[Dict[str, str]]
        :return: The user ID to assign the task to, or None to use current user
        :rtype: Optional[str]
        """
        # If no role is specified, use current user
        if not assign_to_role:
            return None

        # If role mapping is provided and contains the role, use it
        if role_mapping and assign_to_role in role_mapping:
            return role_mapping[assign_to_role]

        # Otherwise, return None to use current user (TaskService default behavior)
        return None
