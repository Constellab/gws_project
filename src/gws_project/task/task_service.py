
from datetime import date
from typing import List, Optional

from gws_core import (BadRequestException, CurrentUserService,
                      ExternalSpaceCreateFolder, Paginator, SearchParams,
                      SpaceService)
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.project.project_security_service import (
    ProjectSecurityService, ProjectUserRole)
from gws_project.project.project_user import ProjectUser
from gws_project.task.task import Task
from gws_project.task.task_dto import (CreateRootTaskDTO, CreateSubTaskDTO,
                                       TaskStatus, UpdateTaskDTO)
from gws_project.task.task_search_builder import TaskSearchBuilder
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

    def search(self, search: SearchParams, page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Task]:
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
        return search_builder.add_search_params(search).search_page(page, number_of_items_per_page)

    @ProjectDbManager.transaction()
    def create_root_task(self, project_id: str, task_dto: CreateRootTaskDTO) -> Task:
        """Create a root task (task without parent) and sync it with Space by creating a child folder.

        :param project_id: The ID of the project
        :type project_id: str
        :param task_dto: The task data to create
        :type task_dto: CreateRootTaskDTO
        :return: The created task with space_folder_id populated
        :rtype: Task
        :raises BadRequestException: If dates are outside project bounds or user is not in project
        """
        # Get the project and ensure it exists
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        # Validate task dates are within project dates
        self._validate_task_dates_within_project(project, task_dto.start_date, task_dto.end_date)

        # Create the task model from DTO
        task = Task()
        task.project = project
        task.parent_task = None  # Root task has no parent
        task.title = task_dto.title
        task.description = task_dto.description
        task.start_date = task_dto.start_date
        task.end_date = task_dto.end_date
        task.status = task_dto.status
        task.priority = task_dto.priority
        task.allow_subtasks = task_dto.allow_subtasks
        task.assign_to = self._validate_assign_to_in_project(project.id, task_dto.assign_to_id)

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
    def create_sub_task(self, parent_task_id: str, task_dto: CreateSubTaskDTO) -> Task:
        """Create a subtask under a parent task. Does not create a folder in Space.
        Only allows creating subtasks under root tasks (no nested subtasks).

        :param parent_task_id: The ID of the parent task
        :type parent_task_id: str
        :param task_dto: The subtask data to create
        :type task_dto: CreateSubTaskDTO
        :return: The created subtask
        :rtype: Task
        :raises BadRequestException: If parent task doesn't allow subtasks, is not a root task,
                                      dates are outside parent task bounds, or user is not in project
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

        # Validate subtask dates are within parent task dates
        self._validate_task_dates_within_parent_task(parent_task, task_dto.start_date, task_dto.end_date)

        # Create the subtask model from DTO
        subtask = Task()
        subtask.project = parent_task.project
        subtask.parent_task = parent_task
        subtask.title = task_dto.title
        subtask.description = task_dto.description
        subtask.start_date = task_dto.start_date
        subtask.end_date = task_dto.end_date
        subtask.status = task_dto.status
        subtask.priority = task_dto.priority
        subtask.allow_subtasks = False  # Subtasks cannot have their own subtasks
        subtask.assign_to = self._validate_assign_to_in_project(parent_task.project.id, task_dto.assign_to_id)

        # Save the subtask to the database
        subtask.save()

        # Note: We do NOT create a folder in Space for subtasks

        return subtask

    @ProjectDbManager.transaction()
    def update_task(self, task_id: str, task_dto: UpdateTaskDTO) -> Task:
        """Update a task. For root tasks, also updates the corresponding folder in Space if the title changes.

        :param task_id: The ID of the task to update
        :type task_id: str
        :param task_dto: The updated task data
        :type task_dto: UpdateTaskDTO
        :return: The updated task
        :rtype: Task
        :raises BadRequestException: If dates are outside valid bounds
        """
        # Get the task and ensure it exists
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Check if title or dates have changed
        folder_has_changed = task.title != task_dto.title or \
            task.start_date != task_dto.start_date or \
            task.end_date != task_dto.end_date

        # Validate dates based on whether this is a root task or subtask
        if task.is_root_task():
            # For root tasks, validate against project dates
            self._validate_task_dates_within_project(task.project, task_dto.start_date, task_dto.end_date)
        else:
            # For subtasks, validate against parent task dates
            self._validate_task_dates_within_parent_task(task.parent_task, task_dto.start_date, task_dto.end_date)

        # Update the task fields from DTO
        task.title = task_dto.title
        task.description = task_dto.description
        task.start_date = task_dto.start_date
        task.end_date = task_dto.end_date
        task.priority = task_dto.priority

        # Save the task to the database
        task.save()

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
        """Update the status of a task and automatically update parent task status if applicable.

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

        # Update the task status
        task.status = status

        # Save the task to the database
        task.save()

        # Update parent task status if this is a subtask
        self._update_parent_task_status(task)

        return task

    @ProjectDbManager.transaction()
    def delete_task(self, task_id: str) -> None:
        """Delete a task. If it's a root task, also deletes all subtasks and the Space folder.

        :param task_id: The ID of the task to delete
        :type task_id: str
        """
        # Get the task and ensure it exists
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # If this is a root task with subtasks, delete all subtasks first
        if task.allow_subtasks:
            # Delete all subtasks (Peewee will handle this via CASCADE on the foreign key)
            # But we'll explicitly query and delete to be clear
            subtasks = task.get_subtasks()
            for subtask in subtasks:
                subtask.delete_instance()

        # Delete the task from the database
        task.delete_instance()

        # If this is a root task with a space folder, delete the folder in Space
        if task.is_root_task() and task.space_folder_id:
            self._space_service.delete_folder(task.space_folder_id)

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

    def _validate_task_dates_within_parent_task(
            self, parent_task: Task, task_start_date: date, task_end_date: date) -> None:
        """Validate that subtask dates are within parent task dates.

        :param parent_task: The parent task
        :type parent_task: Task
        :param task_start_date: Subtask start date
        :type task_start_date: date
        :param task_end_date: Subtask end date
        :type task_end_date: date
        :raises BadRequestException: If dates are outside parent task bounds
        """
        if task_start_date < parent_task.start_date:
            raise BadRequestException(
                f"Subtask start date ({task_start_date}) cannot be before parent task start date ({parent_task.start_date})."
            )
        if task_end_date > parent_task.end_date:
            raise BadRequestException(
                f"Subtask end date ({task_end_date}) cannot be after parent task end date ({parent_task.end_date})."
            )
        if task_start_date > task_end_date:
            raise BadRequestException(
                f"Subtask start date ({task_start_date}) cannot be after its end date ({task_end_date})."
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

    def _calculate_parent_status_from_subtasks(self, parent_task: Task) -> TaskStatus:
        """Calculate the parent task status based on subtask statuses.

        Rules:
        - If any subtask is DOING, parent is DOING
        - If all subtasks are DONE, parent is DONE
        - Otherwise, parent is TODO

        :param parent_task: The parent task
        :type parent_task: Task
        :return: The calculated status
        :rtype: TaskStatus
        """
        subtasks = parent_task.get_subtasks()

        if not subtasks:
            return TaskStatus.TODO

        subtask_statuses = [subtask.status for subtask in subtasks]

        # If any subtask is DOING, parent should be DOING
        if TaskStatus.DOING in subtask_statuses:
            return TaskStatus.DOING

        # If all subtasks are DONE, parent should be DONE
        if all(status == TaskStatus.DONE for status in subtask_statuses):
            return TaskStatus.DONE

        # Otherwise, parent should be TODO
        return TaskStatus.TODO

    def _update_parent_task_status(self, task: Task) -> None:
        """Update the parent task status based on its subtasks if the task has a parent.

        :param task: The task whose parent status should be updated
        :type task: Task
        """
        if task.parent_task:
            new_status = self._calculate_parent_status_from_subtasks(task.parent_task)
            if task.parent_task.status != new_status:
                task.parent_task.status = new_status
                task.parent_task.save()
