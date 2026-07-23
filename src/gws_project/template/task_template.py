


from gws_core import (
    NullableCharField,
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
from gws_project.task.task_dto import TaskPriority
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.task_template_dto import TaskTemplateDTO


class TaskTemplate(ModelWithUser):
    """
    Task template within a project template

    Defines the structure and relationships of tasks to be created
    when a project is instantiated from a template.

    Business rules:
    - start_date_offset: Number of days from project start date
    - duration_days: Length of the task in days
    - assign_to_role: Optional role name for assignment (e.g., 'project_manager', 'team_member')
    """

    project_template = TypedForeignKeyField(
        ProjectTemplate, on_delete='CASCADE', backref='tasks')
    parent_task = NullableForeignKeyField['TaskTemplate'](
        'self', on_delete='CASCADE', backref='subtasks')

    # Task definition fields
    title = TypedCharField(max_length=255)
    description = TypedRichTextDbField()

    # Relative timing (days offset from project start)
    start_date_offset = TypedIntegerField(default=0)  # Days from project start
    duration_days = TypedIntegerField(default=1)  # Task duration in days

    # Creation order, used to list sibling templates in the order they were defined,
    # and copied onto the tasks created from them so they keep this order too.
    order_index = TypedIntegerField(default=0)

    # Task configuration
    priority = TypedEnumField(choices=TaskPriority, max_length=10,
                              default=TaskPriority.MEDIUM)
    allow_subtasks = TypedBooleanField(default=False)

    # Assignment options (optional - can be assigned during project creation)
    assign_to_role = NullableCharField(max_length=100)

    subtasks: list['TaskTemplate']

    def is_root_task(self) -> bool:
        """Check if the template task is a root task (i.e., has no parent task)"""
        return self.parent_task is None

    def is_leaf_task(self) -> bool:
        """Check if the template task is a leaf task (i.e., has no subtasks)"""
        return not self.allow_subtasks

    def get_subtasks(self) -> list['TaskTemplate']:
        """Get the list of subtasks for this template task"""
        return self.subtasks

    def get_ancestors(self) -> list['TaskTemplate']:
        """Get all ancestor task templates from immediate parent up to root task.

        Returns a list of ancestor task templates ordered from immediate parent to root.
        Returns empty list if this is a root task template.

        :return: List of ancestor task templates
        :rtype: List[TaskTemplate]
        """
        ancestors = []
        current = self.parent_task
        while current is not None:
            ancestors.append(current)
            current = current.parent_task
        return ancestors

    def get_all_descendants(self) -> list['TaskTemplate']:
        """Recursively get all descendant task templates (children, grandchildren, etc.).

        Returns a flat list of all task templates in the subtree below this template.
        Returns empty list if this task template has no subtasks.

        :return: List of all descendant task templates
        :rtype: List[TaskTemplate]
        """
        descendants = []
        for subtask in self.get_subtasks():
            descendants.append(subtask)
            # Recursively add descendants of this subtask
            descendants.extend(subtask.get_all_descendants())
        return descendants

    def get_depth(self) -> int:
        """Get the depth of this task template in the hierarchy.

        Root task templates have depth 0, their immediate children have depth 1, etc.

        :return: The depth level of this task template
        :rtype: int
        """
        if self.is_root_task():
            return 0
        else:
            return 1 + self.parent_task.get_depth()

    def get_root_task(self) -> 'TaskTemplate':
        """Get the root task template for this task template.

        If this task template is a root task, returns itself.
        Otherwise, recursively gets the root task template from the parent task.

        :return: The root TaskTemplate
        :rtype: TaskTemplate
        """
        if self.is_root_task():
            return self
        else:
            return self.parent_task.get_root_task()

    @classmethod
    def get_root_tasks_of_template(cls, template_id: str) -> list['TaskTemplate']:
        """Get all root template tasks for a template

        Ordered by start_date_offset (ascending), then by order_index (creation order)
        as a tiebreaker for templates sharing the same offset - not created_at, since
        several templates can be created within the same second.

        :param template_id: The template ID
        :type template_id: str
        :return: List of root template tasks ordered by start offset
        :rtype: List[TaskTemplate]
        """
        return list(cls.select().where(
            (cls.project_template == template_id) & (cls.parent_task.is_null())
        ).order_by(cls.start_date_offset, cls.order_index))

    @classmethod
    def get_subtasks_of_template_task(cls, parent_task_id: str) -> list['TaskTemplate']:
        """Get all subtasks of a parent template task

        Ordered by start_date_offset (ascending), then by order_index (creation order)
        as a tiebreaker for templates sharing the same offset - not created_at, since
        several templates can be created within the same second.

        :param parent_task_id: The parent template task ID
        :type parent_task_id: str
        :return: List of subtasks ordered by start offset
        :rtype: List[TaskTemplate]
        """
        return list(cls.select().where(
            cls.parent_task == parent_task_id
        ).order_by(cls.start_date_offset, cls.order_index))

    def to_dto(self) -> TaskTemplateDTO:
        """Convert the TaskTemplate model to a TaskTemplateDTO for display in the frontend.

        :return: TaskTemplateDTO instance
        :rtype: TaskTemplateDTO
        """
        return TaskTemplateDTO(
            id=self.id,
            project_template_id=self.project_template.id,
            parent_task_id=self.parent_task.id if self.parent_task else None,
            title=self.title,
            description=self.description,
            start_date_offset=self.start_date_offset,
            duration_days=self.duration_days,
            priority=self.priority,
            allow_subtasks=self.allow_subtasks,
            assign_to_role=self.assign_to_role,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
        )

    class Meta:
        table_name = 'gws_project_task_templates'
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
