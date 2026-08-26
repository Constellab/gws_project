from gws_core import (
    NullableCharField,
    NullableDateField,
    NullableForeignKeyField,
    TypedBooleanField,
    TypedCharField,
    TypedEnumField,
    TypedForeignKeyField,
    TypedIntegerField,
    TypedRichTextDbField,
)

from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project import Project
from gws_project.task.task_dto import TaskDTO, TaskPriority, TaskStatus
from gws_project.user.user import User


class Task(ModelWithUser):
    """
    Task model - Manages tasks linked to projects

    Status values: 'BACKLOG', 'TODO' (default), 'DOING', 'DONE',
    Priority values: 'HIGH', 'MEDIUM' (default), 'LOW'

    Business rules:
    - If allow_subtasks = TRUE: status calculated automatically from subtasks
    - If allow_subtasks = FALSE: status managed manually
    - The allow_subtasks field can be changed via TaskService.update_allow_subtasks()
    - Converting parent->leaf is only allowed if the task has no existing subtasks
    """

    project = TypedForeignKeyField(Project, on_delete="CASCADE", backref="+")
    parent_task = NullableForeignKeyField["Task"]("self", on_delete="CASCADE", backref="subtasks")
    title = TypedCharField(max_length=255)
    description = TypedRichTextDbField()
    start_date = NullableDateField()
    due_date = NullableDateField()
    status = TypedEnumField(choices=TaskStatus, max_length=20, default=TaskStatus.TODO)
    priority = TypedEnumField(choices=TaskPriority, max_length=10, default=TaskPriority.MEDIUM)
    allow_subtasks = TypedBooleanField(default=False)
    assign_to = TypedForeignKeyField(User, backref="+")
    # DEPRECATED - unused at runtime. Id of the Space folder that mirrored this
    # root task before documents moved to local storage. Kept only for the
    # MigrateProjectDataFromSpace task; dropped in a later release.
    space_folder_id = NullableCharField(max_length=36)
    progress = TypedIntegerField(default=0)
    # Creation order, used as a tiebreaker when sorting tasks that share the same
    # start_date (e.g. tasks created from a template with the same date offset),
    # so they keep the order they were defined/created in.
    order_index = TypedIntegerField(default=0)

    subtasks: list["Task"]

    def is_root_task(self) -> bool:
        """Check if the task is a root task (i.e., has no parent task)"""
        return self.parent_task is None

    def is_leaf_task(self) -> bool:
        """Check if the task is a leaf task (i.e., has no subtasks)"""
        return not self.allow_subtasks

    def get_subtasks(self) -> list["Task"]:
        """Get the list of subtasks for this task"""
        return self.subtasks

    def _calculate_status_from_subtasks(self) -> bool:
        """Calculate and set the task status based on its subtasks.

        Rules:
        - If any subtask is DOING, set to DOING
        - If all subtasks are DONE, set to DONE
        - If all subtasks are still BACKLOG, set to BACKLOG
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
            # If all subtasks are still BACKLOG, parent stays in BACKLOG too
            elif all(status == TaskStatus.BACKLOG for status in subtask_statuses):
                new_status = TaskStatus.BACKLOG
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
            priority_order = {TaskPriority.HIGH: 3, TaskPriority.MEDIUM: 2, TaskPriority.LOW: 1}
            subtask_priorities = [subtask.priority for subtask in subtasks]

            # Get the highest priority
            new_priority = max(subtask_priorities, key=lambda p: priority_order[p])

        # Check if priority changed
        if self.priority != new_priority:
            self.priority = new_priority
            return True
        return False

    def _calculate_dates_from_subtasks(self) -> bool:
        """Calculate and set the task start and due dates based on its subtasks.

        Sets:
        - Start date: earliest start date of all subtasks (or project start date if no subtasks)
        - Due date: latest due date of all subtasks (or project due date if no subtasks)

        :return: True if any date was changed, False otherwise
        :rtype: bool
        """
        subtasks = self.get_subtasks()

        if not subtasks:
            # Use project dates if no subtasks
            new_start_date = self.project.start_date
            new_due_date = self.project.due_date
        else:
            # Calculate start date: earliest start date from subtasks
            start_dates = [subtask.start_date for subtask in subtasks if subtask.start_date]
            new_start_date = min(start_dates) if start_dates else self.project.start_date

            # Calculate due date: latest due date from subtasks
            due_dates = [subtask.due_date for subtask in subtasks if subtask.due_date]
            new_due_date = max(due_dates) if due_dates else self.project.due_date

        # Check if dates changed
        dates_changed = False
        if self.start_date != new_start_date:
            self.start_date = new_start_date
            dates_changed = True
        if self.due_date != new_due_date:
            self.due_date = new_due_date
            dates_changed = True

        return dates_changed

    def _calculate_progress_from_subtasks(self) -> bool:
        """Calculate and set the task progress based on its subtasks.

        Progress is calculated as the average progress of all subtasks (0-100).
        If there are no subtasks, progress is set to 0.

        :return: True if the progress was changed, False otherwise
        :rtype: bool
        """
        subtasks = self.get_subtasks()

        if not subtasks:
            # No subtasks, set progress to 0
            if self.progress != 0:
                self.progress = 0
                return True
            return False

        # Calculate average progress from all subtasks
        total_progress = sum(subtask.progress for subtask in subtasks)
        new_progress = total_progress // len(subtasks)

        # Check if progress changed
        if self.progress != new_progress:
            self.progress = new_progress
            return True
        return False

    def update_from_subtasks(self) -> bool:
        """Update task dates, status, priority, and progress based on all its subtasks.

        This is the main method to call when subtasks change. It will:
        - Calculate and set dates from subtasks
        - Calculate and set status from subtasks
        - Calculate and set priority from subtasks
        - Calculate and set progress from subtasks

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
        progress_changed = self._calculate_progress_from_subtasks()

        # Return True if any value changed
        return dates_changed or status_changed or priority_changed or progress_changed

    def set_status(self, status: TaskStatus) -> None:
        """Refresh the progress of leaf tasks based on their status.

        Sets progress to 100 if status is DONE, otherwise sets to 0.
        """
        if self.is_leaf_task():
            self.status = status
            if self.status == TaskStatus.DONE:
                self.progress = 100
            else:
                self.progress = 0

    @classmethod
    def get_root_tasks_of_project(cls, project_id: str) -> list["Task"]:
        """Get all tasks associated with a project

        Ordered by start_date, then by order_index (creation order) as a tiebreaker so
        tasks sharing the same start_date (e.g. created from a template with the same
        date offset) keep their original order.

        :param project: The project
        :type project: Project
        :return: List of tasks
        :rtype: List[Task]
        """
        return list(
            cls.select()
            .where((cls.project == project_id) & (cls.parent_task.is_null()))
            .order_by(cls.start_date.is_null(), cls.start_date, cls.order_index)
        )

    @classmethod
    def get_subtasks_of_task(cls, parent_task_id: str) -> list["Task"]:
        """Get all subtasks of a parent task

        Ordered by start_date, then by order_index (creation order) as a tiebreaker so
        tasks sharing the same start_date (e.g. created from a template with the same
        date offset) keep their original order.

        :param parent_task: The parent task
        :type parent_task: Task
        :return: List of subtasks
        :rtype: List[Task]
        """
        return list(
            cls.select()
            .where(cls.parent_task == parent_task_id)
            .order_by(cls.start_date.is_null(), cls.start_date, cls.order_index)
        )

    @classmethod
    def get_tasks_of_user(cls, user_id: str) -> list["Task"]:
        """Get all tasks assigned to a user

        :param user_id: The user ID
        :type user_id: str
        :return: List of tasks
        :rtype: List[Task]
        """
        return list(
            cls.select()
            .where(cls.assign_to == user_id)
            .order_by(cls.start_date.is_null(), cls.start_date)
        )

    @classmethod
    def count_tasks_of_user_in_project(cls, user_id: str, project_id: str) -> int:
        """Count all tasks assigned to a user in a specific project

        :param user_id: The user ID
        :type user_id: str
        :return: Count of tasks
        :rtype: int
        """
        return cls.select().where((cls.assign_to == user_id) & (cls.project == project_id)).count()

    def get_root_task(self) -> "Task":
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

    def get_ancestors(self) -> list["Task"]:
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

    def get_all_descendants(self) -> list["Task"]:
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
            due_date=self.due_date,
            # Language-neutral fallbacks: the display text is rebuilt in the user's
            # language by the app layer (common/date_format.localize_task_dto), which a
            # model cannot do since it knows nothing about the session's language.
            start_date_text=self.start_date.isoformat() if self.start_date else "",
            due_date_text=self.due_date.isoformat() if self.due_date else "",
            status=self.status,
            priority=self.priority,
            allow_subtasks=self.allow_subtasks,
            assign_to=self.assign_to.to_dto(),
            project_id=self.project.id,
            parent_task_id=self.parent_task.id if self.parent_task else None,
            parent_task_title=self.parent_task.title if self.parent_task else None,
            progress=self.progress,
            created_at=self.created_at,
            created_by=self.created_by.to_dto(),
            last_modified_at=self.last_modified_at,
            last_modified_by=self.last_modified_by.to_dto(),
        )

    class Meta:
        table_name = "gws_project_tasks"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
