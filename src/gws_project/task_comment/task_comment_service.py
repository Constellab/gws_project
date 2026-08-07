from gws_core import CurrentUserService, RichTextDTO, UnauthorizedException

from gws_project.core.project_db_manager import ProjectDbManager
from gws_project.project.project_dto import ProjectUserRole
from gws_project.project.project_security_service import ProjectSecurityService
from gws_project.project.project_user import ProjectUser
from gws_project.task_comment.task_comment import TaskComment


class TaskCommentService:
    """Service class for managing comments posted on tasks."""

    @ProjectDbManager.transaction()
    def create_comment(self, task_id: str, content: RichTextDTO) -> TaskComment:
        """Create a comment on a task.

        :param task_id: The ID of the task to comment on
        :type task_id: str
        :param content: The comment's rich text content
        :type content: RichTextDTO
        :return: The created comment
        :rtype: TaskComment
        :raises NotFoundException: If the task is not found
        :raises UnauthorizedException: If the current user doesn't have access to the task
        """
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        comment = TaskComment()
        comment.task = task
        comment.content = content
        comment.save()

        return comment

    def get_comments_of_task(self, task_id: str) -> list[TaskComment]:
        """Get all comments of a task, ordered from oldest to newest.

        :param task_id: The ID of the task
        :type task_id: str
        :return: List of comments
        :rtype: List[TaskComment]
        :raises NotFoundException: If the task is not found
        :raises UnauthorizedException: If the current user doesn't have access to the task
        """
        security_service = ProjectSecurityService()
        task = security_service.get_and_check_role_for_task(task_id, ProjectUserRole.USER)

        return list(
            TaskComment.select()
            .where(TaskComment.task == task.id)
            .order_by(TaskComment.created_at)
        )

    @ProjectDbManager.transaction()
    def update_comment(self, comment_id: str, content: RichTextDTO) -> TaskComment:
        """Update the content of a comment.

        Only the comment's author or a project OWNER can edit it.

        :param comment_id: The ID of the comment to update
        :type comment_id: str
        :param content: The new rich text content
        :type content: RichTextDTO
        :return: The updated comment
        :rtype: TaskComment
        :raises NotFoundException: If the comment is not found
        :raises UnauthorizedException: If the current user cannot edit this comment
        """
        comment = self._get_comment_and_check_edit_permission(comment_id)

        comment.content = content
        comment.save()

        return comment

    def _get_comment_and_check_edit_permission(self, comment_id: str) -> TaskComment:
        """Get a comment and check that the current user is allowed to edit it.

        :param comment_id: The ID of the comment
        :type comment_id: str
        :return: The comment
        :rtype: TaskComment
        :raises NotFoundException: If the comment is not found
        :raises UnauthorizedException: If the current user is neither the comment's
            author nor a project OWNER
        """
        comment = TaskComment.get_by_id_and_check(comment_id)
        current_user = CurrentUserService.get_and_check_current_user()

        is_author = comment.created_by.id == current_user.id
        is_project_owner = ProjectUser.user_has_role(
            comment.task.project.id, current_user.id, ProjectUserRole.OWNER
        )
        if not is_author and not is_project_owner:
            raise UnauthorizedException("You can only edit your own comments.")

        return comment
