from datetime import date, datetime, timedelta

from gws_core import (
    BadRequestException,
    CurrentUserService,
    RichText,
    RichTextDTO,
)
from peewee import fn

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.document.document_service import DocumentService
from gws_project.document.project_document import ProjectDocument
from gws_project.project.project import Project
from gws_project.project.project_count_dto import ChildrenCountDTO
from gws_project.project.project_security_service import ProjectSecurityService, ProjectUserRole
from gws_project.project.project_user import ProjectUser
from gws_project.task.task import Task
from gws_project.task.task_dto import CreateTaskDTO, TaskPriority, TaskStatus, UpdateTaskDTO
from gws_project.template.task_template import TaskTemplate
from gws_project.user.user import User


class TaskService:
    """Service class for managing tasks.

    Tasks and their documents are stored locally (brick DB + dedicated lab
    file store). Space is not involved.
    """

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

    def get_root_tasks_of_project(self, project_id: str) -> list[Task]:
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

        return Task.get_root_tasks_of_project(project.id)

    def get_subtasks(self, parent_task_id: str) -> list[Task]:
        """Get all subtasks of a parent task by parent task ID.

        :param parent_task_id: The ID of the parent task
        :type parent_task_id: str
        :return: List of subtasks if the user has access
        :rtype: List[Task]
        :raises NotFoundException: If the parent task is not found
        :raises UnauthorizedException: If the user doesn't have access to the parent task
        """
        security_service = ProjectSecurityService()
        parent_task = security_service.get_and_check_role_for_task(
            parent_task_id, ProjectUserRole.USER
        )

        return Task.get_subtasks_of_task(parent_task.id)

    def get_task_children_count(self, task_id: str) -> ChildrenCountDTO:
        """Get the number of direct subtasks and documents for a task.

        :param task_id: The ID of the task
        :type task_id: str
        :return: ChildrenCountDTO with subtask_count and document_count
        :rtype: ChildrenCountDTO
        """
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # Count direct subtasks (not recursive)
        subtask_count = Task.select().where(Task.parent_task == task.id).count()

        # Count documents (files and notes) attached to this task
        document_count = ProjectDocument.count_task_documents(task.id)

        return ChildrenCountDTO(
            subtask_count=subtask_count,
            document_count=document_count,
        )

    @ProjectDbManager.transaction()
    def create_root_task(self, project_id: str, task_dto: CreateTaskDTO) -> Task:
        """Create a root task (task without parent).

        :param project_id: The ID of the project
        :type project_id: str
        :param task_dto: The task data to create
        :type task_dto: CreateTaskDTO
        :return: The created task
        :rtype: Task
        :raises BadRequestException: If dates are outside project bounds or user is not in project
        """
        # Get the project and ensure it exists
        security_service = ProjectSecurityService()
        project = security_service.get_and_check_role_for_project(project_id, ProjectUserRole.USER)

        # Validate task dates are within project dates
        self._validate_task_dates_within_project(project, task_dto.start_date, task_dto.end_date)

        # Create the task model from DTO using common method
        task = self._build_task_from_dto(task_dto, project, parent_task=None)

        # Save the task to the database
        task.save()

        return task

    @ProjectDbManager.transaction()
    def create_sub_task(self, parent_task_id: str, task_dto: CreateTaskDTO) -> Task:
        """Create a subtask under a parent task.
        Supports unlimited nesting levels - subtasks can be created under any task that allows subtasks.
        Parent task dates, status, and priority are automatically updated based on all subtasks,
        and these updates propagate up the entire ancestor chain.

        :param parent_task_id: The ID of the parent task
        :type parent_task_id: str
        :param task_dto: The subtask data to create
        :type task_dto: CreateTaskDTO
        :return: The created subtask
        :rtype: Task
        :raises BadRequestException: If parent task doesn't allow subtasks or user is not in project
        """
        # Get the parent task and ensure it exists
        security_service = ProjectSecurityService()
        parent_task = security_service.get_and_check_role_for_task(
            parent_task_id, ProjectUserRole.USER
        )

        # Check that the parent task allows subtasks
        if not parent_task.allow_subtasks:
            raise BadRequestException(
                "Cannot create subtask. The parent task does not allow subtasks. "
                "Set 'allow_subtasks' to true on the parent task."
            )

        # Create the subtask model from DTO using common method
        # Subtasks can have allow_subtasks set based on the DTO (enables unlimited nesting)
        subtask = self._build_task_from_dto(task_dto, parent_task.project, parent_task=parent_task)

        # Save the subtask to the database
        subtask.save()

        # Update parent task information based on all subtasks (including the new one)
        # This will recursively update all ancestors up to the root task
        self._recalculate_parent_info(subtask)

        return subtask

    @ProjectDbManager.transaction()
    def update_task(self, task_id: str, task_dto: UpdateTaskDTO) -> Task:
        """Update a task.

        For subtasks: Updates title, description, dates, and priority, then recalculates all ancestor task info.
        For parent tasks: Only updates title and description. Dates, status, and priority are
                         automatically calculated from subtasks and propagated up the hierarchy.
        For root tasks without subtasks: Updates all fields.

        Changes propagate up the entire hierarchy chain to the root task.

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
        if task.is_leaf_task():
            # For root tasks, validate against project dates
            self._validate_task_dates_within_project(
                task.project, task_dto.start_date, task_dto.end_date
            )

            # Update the task fields from DTO (the form always resends the full desired
            # state, so a missing date here means the user cleared it)
            task.start_date = task_dto.start_date
            task.end_date = task_dto.end_date
            if task_dto.status:
                task.set_status(task_dto.status)
            if task_dto.priority:
                task.priority = task_dto.priority

        task.title = task_dto.title
        if task_dto.assign_to_id is not None:
            task.assign_to = self._validate_assign_to_in_project(
                task.project.id, task_dto.assign_to_id
            )

        # Save the task to the database
        task.save()

        # If this is not a root task, update all ancestor tasks in the hierarchy
        self._recalculate_parent_info(task)

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
        """Update the status of a task and automatically update all ancestor tasks.

        The status change propagates up the entire hierarchy chain, updating all ancestor tasks
        based on their subtasks' statuses.

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
        task.set_status(status)

        # Save the task to the database
        task.save()

        # Update all ancestor tasks in the hierarchy (parent, grandparent, etc.)
        # This updates not just status, but also dates and priority based on all subtasks
        self._recalculate_parent_info(task)

        return task

    @ProjectDbManager.transaction()
    def update_priority(self, task_id: str, priority: TaskPriority) -> Task:
        """Update the priority of a task and automatically update all ancestor tasks.

        The priority change propagates up the entire hierarchy chain, updating all ancestor tasks
        based on their subtasks' priorities.

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

        # Update all ancestor tasks in the hierarchy (parent, grandparent, etc.)
        # This updates not just priority, but also dates and status based on all subtasks
        self._recalculate_parent_info(task)

        return task

    @ProjectDbManager.transaction()
    def update_allow_subtasks(self, task_id: str, allow_subtasks: bool) -> Task:
        """Update whether a task allows subtasks (convert between parent and leaf task).

        Converting to allow_subtasks=True (leaf -> parent):
        - Always allowed since leaf tasks have no children.
        - Status, priority, dates, and progress are recalculated to empty-parent defaults
          (TODO, MEDIUM, project dates, 0 progress) via update_from_subtasks().

        Converting to allow_subtasks=False (parent -> leaf):
        - Only allowed if the task has NO existing subtasks.
        - Progress is adjusted to match the current status: 0 for BACKLOG/TODO/DOING, 100 for DONE.

        After either conversion, the ancestor chain is recalculated.

        :param task_id: The ID of the task to update
        :type task_id: str
        :param allow_subtasks: The new value for allow_subtasks
        :type allow_subtasks: bool
        :return: The updated task
        :rtype: Task
        :raises BadRequestException: If converting parent->leaf and task has existing subtasks
        """
        # Get the task and ensure it exists
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        # No-op if value is already the same
        if task.allow_subtasks == allow_subtasks:
            return task

        if allow_subtasks:
            # Converting leaf -> parent
            task.allow_subtasks = True
            # Reset to empty-parent defaults (auto-calculated mode)
            task.update_from_subtasks()
        else:
            # Converting parent -> leaf: validate no existing subtasks
            existing_subtasks = Task.get_subtasks_of_task(task.id)
            if existing_subtasks:
                raise BadRequestException(
                    "Cannot convert to a normal task because this task has existing subtasks. "
                    "Please delete all subtasks first."
                )
            task.allow_subtasks = False
            # Adjust progress to match status for the new leaf task
            if task.status == TaskStatus.DONE:
                task.progress = 100
            else:
                task.progress = 0

        # Save the task to the database
        task.save()

        # Propagate changes up the ancestor chain
        self._recalculate_parent_info(task)

        return task

    def _resolve_new_parent_task(
        self, task: Task, new_project: Project, new_parent_task_id: str | None
    ) -> Task | None:
        """Resolve and validate the destination parent task for a move operation.

        :param task: The task being moved
        :type task: Task
        :param new_project: The destination project
        :type new_project: Project
        :param new_parent_task_id: The ID of the destination parent task, or None for a root task
        :type new_parent_task_id: Optional[str]
        :return: The destination parent task, or None if moving to a root position
        :rtype: Optional[Task]
        :raises BadRequestException: If the destination parent is invalid
        """
        if not new_parent_task_id:
            return None

        security_service = ProjectSecurityService()
        new_parent_task = security_service.get_and_check_role_for_task(
            new_parent_task_id, ProjectUserRole.USER
        )

        if new_parent_task.id == task.id:
            raise BadRequestException("Cannot move a task under itself.")

        if new_parent_task.project.id != new_project.id:
            raise BadRequestException(
                "The destination parent task must belong to the destination project."
            )

        if not new_parent_task.allow_subtasks:
            raise BadRequestException(
                f"Cannot move the task under '{new_parent_task.title}' because it does not "
                "allow subtasks. Enable subtasks on that task first."
            )

        if task.allow_subtasks:
            descendant_ids = {descendant.id for descendant in task.get_all_descendants()}
            if new_parent_task.id in descendant_ids:
                raise BadRequestException("Cannot move a task under one of its own subtasks.")

        return new_parent_task

    def _validate_move(
        self,
        task: Task,
        new_project: Project,
        new_parent_task: Task | None,
        same_project: bool,
        old_parent_task: Task | None,
    ) -> None:
        """Validate a move operation before it is applied.

        :param task: The task being moved
        :type task: Task
        :param new_project: The destination project
        :type new_project: Project
        :param new_parent_task: The destination parent task, or None for a root task
        :type new_parent_task: Optional[Task]
        :param same_project: Whether the destination project is the same as the current one
        :type same_project: bool
        :param old_parent_task: The task's current parent task, or None if it's a root task
        :type old_parent_task: Optional[Task]
        :raises BadRequestException: If the move is a no-op, or if an assignee (of the task or one
            of its descendants) is not a member of the destination project, or if a leaf task's
            dates fall outside the destination project's bounds
        """
        old_parent_id = old_parent_task.id if old_parent_task else None
        new_parent_id = new_parent_task.id if new_parent_task else None
        if same_project and old_parent_id == new_parent_id:
            raise BadRequestException("The task is already in that location.")

        # Moving to another project: the assignees of the task and all its descendants
        # must be members of the destination project
        if not same_project:
            self._validate_assign_to_in_project(
                new_project.id, task.assign_to.id if task.assign_to else None
            )
            for descendant in task.get_all_descendants():
                self._validate_assign_to_in_project(
                    new_project.id, descendant.assign_to.id if descendant.assign_to else None
                )

        # A leaf task becoming a root task must respect the destination project's date bounds
        # (parent tasks have their dates auto-calculated from subtasks, so no check for them)
        if new_parent_task is None and task.is_leaf_task():
            self._validate_task_dates_within_project(new_project, task.start_date, task.end_date)

    @ProjectDbManager.transaction()
    def move_task(
        self, task_id: str, new_project_id: str, new_parent_task_id: str | None
    ) -> Task:
        """Move a task to a new project and/or under a new parent task.

        This supports every combination:
        - Promote a subtask to a root task (new_parent_task_id=None), in the same or another project
        - Move a root task under a task with subtasks, in the same or another project
        - Re-parent a subtask under another task, in the same or another project
        - Move a task (and its whole subtree, if any) to another project without changing its parent

        The old and new ancestor chains (and project progress) are recalculated after the move.

        :param task_id: The ID of the task to move
        :type task_id: str
        :param new_project_id: The ID of the destination project
        :type new_project_id: str
        :param new_parent_task_id: The ID of the destination parent task, or None to make it a root task
        :type new_parent_task_id: Optional[str]
        :return: The moved task
        :rtype: Task
        :raises BadRequestException: If the destination is invalid (cycle, wrong project, parent
            doesn't allow subtasks, assignees not in the destination project, or no-op move)
        :raises NotFoundException: If the task, destination project, or destination parent is not found
        :raises UnauthorizedException: If the user doesn't have access to the task or destination project
        """
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)
        new_project = security_service.get_and_check_role_for_project(
            new_project_id, ProjectUserRole.USER
        )
        new_parent_task = self._resolve_new_parent_task(task, new_project, new_parent_task_id)

        old_parent_task = task.parent_task
        old_project = task.project
        same_project = old_project.id == new_project.id
        self._validate_move(task, new_project, new_parent_task, same_project, old_parent_task)

        task.project = new_project
        task.parent_task = new_parent_task
        task.save()

        # The whole subtree moves along with the task when the project changes
        if not same_project:
            for descendant in task.get_all_descendants():
                descendant.project = new_project
                descendant.save()

        # Recalculate the old side: the old parent lost a subtask, or the old project's
        # root task set changed
        if old_parent_task:
            self._recalculate_task_chain(old_parent_task)
        else:
            self._recalculate_project_progress(old_project)

        # Recalculate the new side: the new parent gained a subtask, or the new project's
        # root task set changed
        if new_parent_task:
            self._recalculate_task_chain(new_parent_task)
        else:
            self._recalculate_project_progress(new_project)

        return task

    def get_navigable_child_tasks(
        self, project_id: str, parent_task_id: str | None, exclude_task_id: str | None = None
    ) -> list[Task]:
        """Get the child "folder" tasks at one level of the task hierarchy: either the
        root tasks of a project (if `parent_task_id` is None) or the subtasks of a given
        parent task, keeping only tasks that themselves allow subtasks (so they can be
        browsed into further or used as a destination).

        Powers the hierarchical folder-style browser used to move a task: excludes
        `exclude_task_id` and all of its descendants, since moving a task under itself or
        one of its own subtasks would create a cycle.

        :param project_id: The ID of the project being browsed
        :type project_id: str
        :param parent_task_id: The ID of the parent task to list subtasks of, or None to
            list the project's root tasks
        :type parent_task_id: Optional[str]
        :param exclude_task_id: A task ID to exclude, along with its descendants
        :type exclude_task_id: Optional[str]
        :return: List of child tasks that allow subtasks
        :rtype: List[Task]
        """
        security_service = ProjectSecurityService()

        if parent_task_id:
            parent_task = security_service.get_and_check_role_for_task(
                parent_task_id, ProjectUserRole.USER
            )
            if parent_task.project.id != project_id:
                raise BadRequestException("The parent task does not belong to the given project.")
            children = Task.get_subtasks_of_task(parent_task.id)
        else:
            project = security_service.get_and_check_role_for_project(
                project_id, ProjectUserRole.USER
            )
            children = Task.get_root_tasks_of_project(project.id)

        excluded_ids: set[str] = set()
        if exclude_task_id:
            excluded_ids.add(exclude_task_id)
            excluded_task = Task.get_by_id(exclude_task_id)
            if excluded_task:
                excluded_ids.update(
                    descendant.id for descendant in excluded_task.get_all_descendants()
                )

        return [task for task in children if task.allow_subtasks and task.id not in excluded_ids]

    @ProjectDbManager.transaction()
    def delete_task(self, task_id: str) -> None:
        """Delete a task and all its descendants recursively, along with their
        documents (hard delete, the documents and their files cannot be recovered).

        For tasks with subtasks: Deletes all descendants at all levels (children, grandchildren, etc.)
        For subtasks: Updates all ancestor tasks after deletion

        :param task_id: The ID of the task to delete
        :type task_id: str
        """
        # Get the task and ensure it exists
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        descendants = task.get_all_descendants()

        # Delete the documents (and their files in the store) of the task and
        # its descendants. The DB CASCADE would remove the rows but not the
        # file nodes on disk.
        DocumentService().delete_documents_of_tasks([task] + descendants)

        # If this task has subtasks, delete all descendants recursively
        # The database CASCADE on the foreign key will handle this automatically,
        # but we can also use get_all_descendants() if we need to perform
        # additional operations on each descendant before deletion
        if task.allow_subtasks:
            # Delete in reverse order (deepest first) to maintain referential integrity
            for descendant in reversed(descendants):
                descendant.delete_instance()

        # Delete the task from the database
        task.delete_instance()

        # Recursively update ancestors
        self._recalculate_parent_info(task)

    def _validate_task_dates_within_project(
        self, project: Project, task_start_date: date | None, task_end_date: date | None
    ) -> None:
        """Validate that task dates are within project dates.

        Task dates are optional: any check involving a missing date is skipped.

        :param project: The project
        :type project: Project
        :param task_start_date: Task start date, if set
        :type task_start_date: Optional[date]
        :param task_end_date: Task end date, if set
        :type task_end_date: Optional[date]
        :raises BadRequestException: If dates are outside project bounds
        """
        if task_start_date is not None and task_start_date < project.start_date:
            raise BadRequestException(
                f"Task start date ({task_start_date}) cannot be before project start date ({project.start_date})."
            )
        if task_end_date is not None and task_end_date > project.end_date:
            raise BadRequestException(
                f"Task end date ({task_end_date}) cannot be after project end date ({project.end_date})."
            )
        if (
            task_start_date is not None
            and task_end_date is not None
            and task_start_date > task_end_date
        ):
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
        parent_task: Task | None = None,
        force_allow_subtasks: bool | None = None,
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
        # Creation order, used as a tiebreaker so tasks sharing the same start_date
        # (e.g. created from a template with the same date offset) keep their order
        task.order_index = self._get_next_order_index()

        # Set dates (optional - a task may have no dates, only a start, only an end, or both)
        task.start_date = task_dto.start_date
        task.end_date = task_dto.end_date

        # Set status and priority with defaults
        task.set_status(task_dto.status or TaskStatus.TODO)
        task.priority = task_dto.priority or TaskPriority.MEDIUM

        # Set allow_subtasks - can be forced (for subtasks) or from DTO
        if force_allow_subtasks is not None:
            task.allow_subtasks = force_allow_subtasks
        else:
            task.allow_subtasks = task_dto.allow_subtasks

        # Validate and set assigned user
        task.assign_to = self._validate_assign_to_in_project(project.id, task_dto.assign_to_id)

        return task

    def _get_next_order_index(self) -> int:
        """Get the next order_index value to assign to a newly created task.

        A single, brick-wide increasing counter is enough: order_index is only ever
        compared between tasks that are already scoped to the same listing (same
        project root level, or same parent's subtasks), so it just needs to reflect
        relative creation order within any such group.

        :return: The next order_index value
        :rtype: int
        """
        max_order_index = Task.select(fn.MAX(Task.order_index)).scalar()
        return (max_order_index or 0) + 1

    def _recalculate_parent_info(self, task: Task) -> None:
        """Update parent task information (dates, status, priority, progress) based on all its subtasks.

        This method recursively updates the entire ancestor chain up to the root task.
        For each ancestor task, it automatically calculates:
        - Start date: earliest start date of all subtasks (or project start date if no subtasks)
        - End date: latest end date of all subtasks (or project end date if no subtasks)
        - Status: based on subtask statuses (or TODO if no subtasks)
        - Priority: highest priority among all subtasks (or MEDIUM if no subtasks)
        - Progress: average progress of all subtasks

        Only saves to database if there were actual changes.
        After updating the root task, recalculates project progress.

        :param parent_task: The parent task to update (and all its ancestors)
        :type parent_task: Task
        """

        if task.parent_task:
            parent_task = task.parent_task
            # Update from subtasks (calculates dates, status, priority, and progress)
            has_changes = parent_task.update_from_subtasks()

            # Only save if there were changes
            if has_changes:
                # Save the updated parent task
                parent_task.save()

            # Recursively update the parent's parent (if it exists)
            # This ensures all ancestors in the hierarchy are updated
            self._recalculate_parent_info(parent_task)

        else:
            # If this is a root task, recalculate project progress
            self._recalculate_project_progress(task.project)

    def _recalculate_task_chain(self, task: Task) -> None:
        """Recalculate `task` itself from its subtasks, then its whole ancestor chain.

        Unlike `_recalculate_parent_info` (which starts from the ancestors of the task
        that was directly modified), this starts at `task` itself. Used after moving a
        task, where `task` is the old/new parent whose subtask set just changed (not the
        moved task, whose own values are unaffected by the move).

        :param task: The task to recalculate (and all its ancestors)
        :type task: Task
        """
        if task.allow_subtasks:
            has_changes = task.update_from_subtasks()
            if has_changes:
                task.save()

        if task.parent_task:
            self._recalculate_task_chain(task.parent_task)
        else:
            self._recalculate_project_progress(task.project)

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

    def get_descendants_assigned_users(self, task_id: str) -> list[User]:
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

        descendants = task.get_all_descendants()

        # Extract unique users using a dictionary to preserve order and avoid duplicates
        seen_user_ids = set()
        unique_users = []

        for descendant in descendants:
            if descendant.assign_to and descendant.assign_to.id not in seen_user_ids:
                seen_user_ids.add(descendant.assign_to.id)
                unique_users.append(descendant.assign_to)

        return unique_users

    def create_task_from_template(
        self,
        project: Project,
        task_template: TaskTemplate,
        project_start_date: date,
        role_mapping: dict[str, str] | None = None,
        parent_task: Task | None = None,
    ) -> Task:
        """Create a task from a task template with unlimited hierarchy support.

        Recursively creates all descendant tasks (subtasks, sub-subtasks, etc.) from the template,
        supporting unlimited nesting levels. The entire task hierarchy is created in a single operation.

        :param project: The project to create the task in
        :type project: Project
        :param task_template: The task template to create the task from
        :type task_template: TaskTemplate
        :param project_start_date: The project start date for calculating task dates
        :type project_start_date: date
        :param role_mapping: Dictionary mapping role names to user IDs
        :type role_mapping: Optional[Dict[str, str]]
        :param parent_task: The parent task if this is a subtask (for recursive calls)
        :type parent_task: Optional[Task]
        :return: The created task
        :rtype: Task
        """
        # Calculate task dates based on template offsets. No offset means no dates at
        # all (duration alone can't anchor an end date without a start).
        task_start_date = (
            project_start_date + timedelta(days=task_template.start_date_offset)
            if task_template.start_date_offset is not None
            else None
        )
        # Subtract 1 because duration includes the start day
        task_end_date = (
            task_start_date + timedelta(days=max(task_template.duration_days - 1, 0))
            if task_start_date is not None and task_template.duration_days is not None
            else None
        )

        # Determine the user to assign the task to using role mapping
        assign_to_user_id = self._get_assign_to_user_id_from_role(
            task_template.assign_to_role, role_mapping
        )

        # Tasks that aren't due to start yet are created in the Backlog rather than TODO,
        # since a batch of template-generated tasks hasn't been individually reviewed yet.
        # Tasks starting today or earlier are actionable right away, so they stay in TODO.
        # A task with no start date has nothing to be "not due yet" against, so it also
        # stays in TODO.
        # project_start_date may be a date or a datetime depending on the caller, and
        # datetime disallows direct comparison with a plain date, so normalize first.
        if task_start_date is None:
            initial_status = TaskStatus.TODO
        else:
            task_start_date_only = (
                task_start_date.date() if isinstance(task_start_date, datetime) else task_start_date
            )
            initial_status = (
                TaskStatus.BACKLOG if task_start_date_only > date.today() else TaskStatus.TODO
            )

        # Create task DTO
        task_dto = CreateTaskDTO(
            title=task_template.title,
            start_date=task_start_date,
            end_date=task_end_date,
            status=initial_status,
            priority=task_template.priority,
            allow_subtasks=task_template.allow_subtasks,
            assign_to_id=assign_to_user_id,
        )

        # Create the task using TaskService methods
        if parent_task is None:
            # Create root task
            task = self.create_root_task(project.id, task_dto)
        else:
            # By default use the parent task's assignee if none specified
            if not task_dto.assign_to_id:
                task_dto.assign_to_id = parent_task.assign_to.id if parent_task.assign_to else None
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
                project, subtask_template, project_start_date, role_mapping, task
            )

        return task

    def _get_assign_to_user_id_from_role(
        self, assign_to_role: str | None, role_mapping: dict[str, str] | None = None
    ) -> str | None:
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

    def _recalculate_project_progress(self, project: Project) -> Project:
        """Recalculate and update project progress based on direct children (root tasks) progress.

        The project progress is calculated as the average progress of all root tasks.
        If there are no root tasks, progress is set to 0.

        :param project: The project to update
        :type project: Project
        :return: The updated project
        :rtype: Project
        :raises NotFoundException: If the project is not found
        :raises UnauthorizedException: If the user doesn't have access to the project
        """
        # Get the project and ensure it exists

        # Get all root tasks for this project
        root_tasks = Task.get_root_tasks_of_project(project.id)

        if not root_tasks:
            # No root tasks, set progress to 0
            project.progress = 0
        else:
            # Calculate average progress from all root tasks
            total_progress = sum(task.progress for task in root_tasks)
            project.progress = total_progress // len(root_tasks)

        # Save the updated project
        project.save()

        return project
