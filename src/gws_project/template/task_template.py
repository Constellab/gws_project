

from typing import List

from gws_core import EnumField, RichTextDbField, RichTextDTO
from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.task.task_dto import TaskPriority
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.task_template_dto import TaskTemplateDTO
from peewee import BooleanField, CharField, ForeignKeyField, IntegerField


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

    project_template = ForeignKeyField(
        ProjectTemplate, on_delete='CASCADE', null=False, backref='tasks')
    parent_task: 'TaskTemplate' = ForeignKeyField(
        'self', on_delete='CASCADE', null=True, backref='subtasks')

    # Task definition fields
    title = CharField(max_length=255, null=False)
    description: RichTextDTO = RichTextDbField(null=False)

    # Relative timing (days offset from project start)
    start_date_offset = IntegerField(default=0)  # Days from project start
    duration_days = IntegerField(default=1)  # Task duration in days

    # Task configuration
    priority = EnumField(choices=TaskPriority, max_length=10,
                         default=TaskPriority.MEDIUM, null=False)
    allow_subtasks = BooleanField(default=False)

    # Assignment options (optional - can be assigned during project creation)
    assign_to_role = CharField(max_length=100, null=True)

    subtasks: List['TaskTemplate']

    def is_root_task(self) -> bool:
        """Check if the template task is a root task (i.e., has no parent task)"""
        return self.parent_task is None

    def is_leaf_task(self) -> bool:
        """Check if the template task is a leaf task (i.e., has no subtasks)"""
        return not self.allow_subtasks

    def get_subtasks(self) -> List['TaskTemplate']:
        """Get the list of subtasks for this template task"""
        return self.subtasks

    @classmethod
    def get_root_tasks_of_template(cls, template_id: str) -> List['TaskTemplate']:
        """Get all root template tasks for a template

        :param template_id: The template ID
        :type template_id: str
        :return: List of root template tasks ordered by created_at
        :rtype: List[TaskTemplate]
        """
        return list(cls.select().where(
            (cls.project_template == template_id) & (cls.parent_task.is_null())
        ).order_by(cls.created_at))

    @classmethod
    def get_subtasks_of_template_task(cls, parent_task_id: str) -> List['TaskTemplate']:
        """Get all subtasks of a parent template task

        :param parent_task_id: The parent template task ID
        :type parent_task_id: str
        :return: List of subtasks ordered by created_at
        :rtype: List[TaskTemplate]
        """
        return list(cls.select().where(
            cls.parent_task == parent_task_id
        ).order_by(cls.created_at))

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
