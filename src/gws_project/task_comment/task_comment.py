from gws_core import TypedForeignKeyField, TypedRichTextDbField

from gws_project.core.model_with_user import ModelWithUser
from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.task.task import Task
from gws_project.task_comment.task_comment_dto import TaskCommentDTO


class TaskComment(ModelWithUser):
    """
    TaskComment model - A comment posted on a task, displayed interleaved with the
    task's history events (like a GitHub issue timeline).
    """

    task = TypedForeignKeyField(Task, on_delete="CASCADE", backref="comments")
    content = TypedRichTextDbField()

    def _before_insert(self) -> None:
        super()._before_insert()
        # created_at/last_modified_at each resolve their own default independently
        # (two separate now() calls), so they can differ by a few microseconds even
        # though the comment was never edited. Force them equal at creation time so
        # `is_edited` (last_modified_at != created_at) starts out reliably False.
        self.last_modified_at = self.created_at

    def to_dto(self) -> TaskCommentDTO:
        """Convert the TaskComment model to a TaskCommentDTO for display in the frontend.

        :return: TaskCommentDTO instance
        :rtype: TaskCommentDTO
        """
        return TaskCommentDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            task_id=self.task.id,
            content=self.content,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            is_edited=self.last_modified_at != self.created_at,
        )

    class Meta:
        table_name = "gws_project_task_comments"
        database = ProjectDbManager.get_instance().db
        is_table = True
        db_manager = ProjectDbManager.get_instance()
