

from typing import List

from gws_core import EnumField, RichTextDbField, RichTextDTO, Tag
from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.task.task_dto import TaskDTO, TaskPriority, TaskStatus
from gws_project.user.user import User
from peewee import BooleanField, CharField, DateField, ForeignKeyField


class Task(ModelWithUser):
    """
    Task model - Manages tasks linked to projects

    Status values: 'TODO' (default), 'DOING', 'DONE',
    Priority values: 'HIGH', 'MEDIUM' (default), 'LOW'

    Business rules:
    - If allow_subtasks = TRUE: status calculated automatically from subtasks
    - If allow_subtasks = FALSE: status managed manually
    - The allow_subtasks field cannot be modified after creation
    """

    project = ForeignKeyField(
        Project, on_delete='CASCADE', null=False, backref='+')
    parent_task: 'Task' = ForeignKeyField(
        'self', on_delete='CASCADE', null=True, backref='subtasks')
    title = CharField(max_length=255, null=False)
    description: RichTextDTO = RichTextDbField(null=False)
    start_date = DateField(null=False)
    end_date = DateField(null=False)
    status = EnumField(choices=TaskStatus, max_length=20,
                       default=TaskStatus.TODO, null=False)
    priority = EnumField(choices=TaskPriority, max_length=10,
                         default=TaskPriority.MEDIUM, null=False)
    allow_subtasks = BooleanField(default=False)
    assign_to = ForeignKeyField(User, null=False, backref='+')
    space_folder_id = CharField(max_length=36, null=True)

    subtasks: List['Task']

    SPACE_TASK_NAME: str = 'task'

    def is_root_task(self) -> bool:
        """Check if the task is a root task (i.e., has no parent task)"""
        return self.parent_task is None

    def is_leaf_task(self) -> bool:
        """Check if the task is a leaf task (i.e., has no subtasks)"""
        return not self.allow_subtasks

    def get_subtasks(self) -> List['Task']:
        """Get the list of subtasks for this task"""
        return self.subtasks

    def _calculate_status_from_subtasks(self) -> bool:
        """Calculate and set the task status based on its subtasks.

        Rules:
        - If any subtask is DOING, set to DOING
        - If all subtasks are DONE, set to DONE
        - Otherwise, set to TODO

        :return: True if the status was changed, False otherwise
        :rtype: bool
        """
        subtasks = self.get_subtasks()

        if not subtasks:
            new_status = TaskStatus.TODO
        else:
            subtask_statuses = [subtask.status for subtask in subtasks]

            # If any subtask is DOING, parent should be DOING
            if TaskStatus.DOING in subtask_statuses:
                new_status = TaskStatus.DOING
            # If all subtasks are DONE, parent should be DONE
            elif all(status == TaskStatus.DONE for status in subtask_statuses):
                new_status = TaskStatus.DONE
            # Otherwise, parent should be TODO
            else:
                new_status = TaskStatus.TODO

        # Check if status changed
        if self.status != new_status:
            self.status = new_status
            return True
        return False

    def _calculate_priority_from_subtasks(self) -> bool:
        """Calculate and set the task priority based on its subtasks.

        Sets to the highest priority among all subtasks (HIGH > MEDIUM > LOW).

        :return: True if the priority was changed, False otherwise
        :rtype: bool
        """
        subtasks = self.get_subtasks()

        if not subtasks:
            new_priority = TaskPriority.MEDIUM
        else:
            # Define priority order
            priority_order = {TaskPriority.HIGH: 3,
                              TaskPriority.MEDIUM: 2, TaskPriority.LOW: 1}
            subtask_priorities = [subtask.priority for subtask in subtasks]

            # Get the highest priority
            new_priority = max(subtask_priorities,
                               key=lambda p: priority_order[p])

        # Check if priority changed
        if self.priority != new_priority:
            self.priority = new_priority
            return True
        return False

    def _calculate_dates_from_subtasks(self) -> bool:
        """Calculate and set the task start and end dates based on its subtasks.

        Sets:
        - Start date: earliest start date of all subtasks (or project start date if no subtasks)
        - End date: latest end date of all subtasks (or project end date if no subtasks)

        :return: True if any date was changed, False otherwise
        :rtype: bool
        """
        subtasks = self.get_subtasks()

        if not subtasks:
            # Use project dates if no subtasks
            new_start_date = self.project.start_date
            new_end_date = self.project.end_date
        else:
            # Calculate start date: earliest start date from subtasks
            start_dates = [
                subtask.start_date for subtask in subtasks if subtask.start_date]
            new_start_date = min(
                start_dates) if start_dates else self.project.start_date

            # Calculate end date: latest end date from subtasks
            end_dates = [
                subtask.end_date for subtask in subtasks if subtask.end_date]
            new_end_date = max(
                end_dates) if end_dates else self.project.end_date

        # Check if dates changed
        dates_changed = False
        if self.start_date != new_start_date:
            self.start_date = new_start_date
            dates_changed = True
        if self.end_date != new_end_date:
            self.end_date = new_end_date
            dates_changed = True

        return dates_changed

    def update_from_subtasks(self) -> bool:
        """Update task dates, status, and priority based on all its subtasks.

        This is the main method to call when subtasks change. It will:
        - Calculate and set dates from subtasks
        - Calculate and set status from subtasks
        - Calculate and set priority from subtasks

        :return: True if any value was changed, False otherwise
        :rtype: bool
        """

        if not self.allow_subtasks:
            # No need to calculate if subtasks are not allowed
            return False
        # Track if any changes were made
        dates_changed = self._calculate_dates_from_subtasks()
        status_changed = self._calculate_status_from_subtasks()
        priority_changed = self._calculate_priority_from_subtasks()

        # Return True if any value changed
        return dates_changed or status_changed or priority_changed

    @classmethod
    def get_root_tasks_of_project(cls, project_id: str) -> List['Task']:
        """Get all tasks associated with a project

        :param project: The project
        :type project: Project
        :return: List of tasks
        :rtype: List[Task]
        """
        return list(cls.select().where((cls.project == project_id) & (cls.parent_task.is_null())).order_by(cls.created_at))

    @classmethod
    def get_subtasks_of_task(cls, parent_task_id: str) -> List['Task']:
        """Get all subtasks of a parent task

        :param parent_task: The parent task
        :type parent_task: Task
        :return: List of subtasks
        :rtype: List[Task]
        """
        return list(cls.select().where(cls.parent_task == parent_task_id).order_by(cls.created_at))

    @classmethod
    def get_tasks_of_user(cls, user_id: str) -> List['Task']:
        """Get all tasks assigned to a user

        :param user_id: The user ID
        :type user_id: str
        :return: List of tasks
        :rtype: List[Task]
        """
        return list(cls.select().where(cls.assign_to == user_id).order_by(cls.created_at))

    @classmethod
    def count_tasks_of_user_in_project(cls, user_id: str, project_id: str) -> int:
        """Count all tasks assigned to a user in a specific project

        :param user_id: The user ID
        :type user_id: str
        :return: Count of tasks
        :rtype: int
        """
        return cls.select().where((cls.assign_to == user_id) & (cls.project == project_id)).count()

    def get_space_folder_id(self) -> str | None:
        """Get the space folder ID for this task.

        For root tasks, returns the task's own space_folder_id.
        For child tasks, recursively gets the space_folder_id from the parent task.

        :return: The space folder ID, or None if no folder is assigned
        :rtype: str | None
        """
        if self.is_root_task():
            return self.space_folder_id
        else:
            return self.parent_task.get_space_folder_id()

    def get_root_task(self) -> 'Task':
        """Get the root task for this task.

        If this task is a root task, returns itself.
        Otherwise, recursively gets the root task from the parent task.

        :return: The root Task
        :rtype: Task
        """
        if self.is_root_task():
            return self
        else:
            return self.parent_task.get_root_task()

    def get_ancestors(self) -> List['Task']:
        """Get all ancestor tasks from immediate parent up to root task.

        Returns a list of ancestor tasks ordered from immediate parent to root.
        Returns empty list if this is a root task.

        :return: List of ancestor tasks
        :rtype: List[Task]
        """
        ancestors = []
        current = self.parent_task
        while current is not None:
            ancestors.append(current)
            current = current.parent_task
        return ancestors

    def get_all_descendants(self) -> List['Task']:
        """Recursively get all descendant tasks (children, grandchildren, etc.).

        Returns a flat list of all tasks in the subtree below this task.
        Returns empty list if this task has no subtasks.

        :return: List of all descendant tasks
        :rtype: List[Task]
        """
        descendants = []
        for subtask in self.get_subtasks():
            descendants.append(subtask)
            # Recursively add descendants of this subtask
            descendants.extend(subtask.get_all_descendants())
        return descendants

    def get_depth(self) -> int:
        """Get the depth of this task in the hierarchy.

        Root tasks have depth 0, their immediate children have depth 1, etc.

        :return: The depth level of this task
        :rtype: int
        """
        if self.is_root_task():
            return 0
        else:
            return 1 + self.parent_task.get_depth()

    def get_space_tag(self) -> Tag:
        return Tag(key=self.SPACE_TASK_NAME, value=self.id)

    def to_dto(self) -> TaskDTO:
        """Convert the Task model to a TaskDTO for display in the frontend.

        :return: TaskDTO instance
        :rtype: TaskDTO
        """
        return TaskDTO(
            id=self.id,
            title=self.title,
            description=self.description,
            start_date=self.start_date,
            end_date=self.end_date,
            status=self.status,
            priority=self.priority,
            allow_subtasks=self.allow_subtasks,
            assign_to=self.assign_to.to_dto(),
            project_id=self.project.id,
            parent_task_id=self.parent_task.id if self.parent_task else None,
            parent_task_title=self.parent_task.title if self.parent_task else None,
            space_folder_id=self.space_folder_id,
            created_at=self.created_at,
            created_by=self.created_by.to_dto(),
            last_modified_at=self.last_modified_at,
            last_modified_by=self.last_modified_by.to_dto()
        )

    class Meta:
        table_name = 'gws_project_tasks'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
