import reflex as rx
from gws_core import RichText, RichTextDTO
from gws_project.project.project_dto import ProjectUserRole
from gws_project.project.project_user import ProjectUser
from gws_project.task_comment.task_comment_dto import TaskCommentDTO
from gws_project.task_comment.task_comment_service import TaskCommentService
from gws_project.task_history.task_history_event_dto import TaskHistoryEventDTO
from gws_project.task_history.task_history_service import TaskHistoryService
from gws_reflex_main import I18nState, ReflexMainState, toast_tr

from ..common.date_format import format_datetime
from ..common.projects.project_page_state import ProjectPageState
from ..common.tasks import (
    task_actions_translations,  # noqa: F401  (side effect: registers translations)
)
from ..common.tasks.task_history_message import HistorySubject, build_history_message
from .activity_item_dto import ActivityItemDTO


class TaskActivityState(rx.State):
    """State for the task Activity tab: the history timeline interleaved with comments.

    Events and comments are fetched once on mount into local lists (`_events`/
    `_comments`), then kept in sync by explicitly updating those lists after each
    create/update. This mirrors the pattern used by TaskListState and
    DocumentsListState elsewhere in this app, instead of re-querying the database
    from a computed var on every render — the latter doesn't reliably push an
    update to the frontend when a handler doesn't otherwise mutate a plain var.

    Comments cannot be deleted, only edited (by their author or a project OWNER).
    """

    _events: list[TaskHistoryEventDTO] = []
    _comments: list[TaskCommentDTO] = []
    _current_user_id: str = ""
    _is_project_owner: bool = False

    new_comment_content: RichTextDTO = RichText().to_dto()
    is_posting_comment: bool = False

    editing_comment_id: str = ""
    edit_comment_content: RichTextDTO = RichText().to_dto()

    @rx.event
    async def refresh_activity(self):
        """Re-fetch this task's history events and comments from the database.

        Called by other states (e.g. TaskDetailState) after they log a change on the
        task (status, title, priority, dates, assignee, move, type, description), so
        the Activity tab reflects it without needing to be remounted.
        """
        project_page_state = await self.get_state(ProjectPageState)
        task = await project_page_state.task()
        if not task:
            return

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            self._events = [
                event.to_dto() for event in TaskHistoryService().get_events_of_task(task.id)
            ]
            self._comments = [
                comment.to_dto()
                for comment in TaskCommentService().get_comments_of_task(task.id)
            ]
            current_user = await main_state.get_and_check_current_user()
            self._current_user_id = current_user.id
            self._is_project_owner = ProjectUser.user_has_role(
                task.project.id, current_user.id, ProjectUserRole.OWNER
            )

    @rx.event(background=True)  # type: ignore
    async def fetch_activity_on_mount(self):
        """Load the current task's history events and comments once on mount."""
        async with self:
            project_page_state = await self.get_state(ProjectPageState)
            task = await project_page_state.task()
            main_state = await self.get_state(ReflexMainState)

            if not task:
                return

        try:
            with await main_state.authenticate_user():
                events = [
                    event.to_dto() for event in TaskHistoryService().get_events_of_task(task.id)
                ]
                comments = [
                    comment.to_dto()
                    for comment in TaskCommentService().get_comments_of_task(task.id)
                ]
                current_user = await main_state.get_and_check_current_user()
                is_owner = ProjectUser.user_has_role(
                    task.project.id, current_user.id, ProjectUserRole.OWNER
                )

            async with self:
                self._events = events
                self._comments = comments
                self._current_user_id = current_user.id
                self._is_project_owner = is_owner
        except Exception as e:
            async with self:
                self._events = []
                self._comments = []
            raise e

    @rx.var
    async def activity_items(self) -> list[ActivityItemDTO]:
        """Return the merged, chronologically sorted timeline of events and comments.

        Both kinds carry a real `created_at`, formatted here in the active language
        rather than by the backend, which knows nothing about the session.

        :return: List of activity items
        :rtype: List[ActivityItemDTO]
        """
        i18n = await self.get_state(I18nState)
        lang = i18n.lang

        items = [
            ActivityItemDTO(
                id=event.id,
                kind="event",
                sort_key=event.created_at,
                actor=event.actor,
                created_at_text=format_datetime(event.created_at, lang),
                message=build_history_message(
                    event_type=event.event_type,
                    old_value=event.old_value,
                    new_value=event.new_value,
                    is_automatic=event.is_automatic,
                    subject=HistorySubject.TIMELINE,
                    i18n=i18n,
                ),
                icon=event.icon,
                is_automatic=event.is_automatic,
            )
            for event in self._events
        ]
        items += [
            ActivityItemDTO(
                id=comment.id,
                kind="comment",
                sort_key=comment.created_at,
                actor=comment.created_by,
                created_at_text=format_datetime(comment.created_at, lang),
                comment_id=comment.id,
                content=comment.content,
                is_edited=comment.is_edited,
                can_edit=self._is_project_owner or comment.created_by.id == self._current_user_id,
            )
            for comment in self._comments
        ]
        items.sort(key=lambda item: item.sort_key)
        return items

    @rx.event
    def handle_new_comment_change(self, event_data: dict):
        """Update the draft content of the new-comment composer.

        :param event_data: The RichTextDTO data emitted by the rich text editor
        :type event_data: dict
        """
        self.new_comment_content = RichTextDTO.from_json(event_data)

    @rx.event
    async def submit_comment(self):
        """Post the drafted comment on the current task and reset the composer."""
        project_page_state = await self.get_state(ProjectPageState)
        task = await project_page_state.task()
        if not task:
            yield await toast_tr.error(self, "task_actions.toast.not_found")
            return

        self.is_posting_comment = True
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            comment = TaskCommentService().create_comment(task.id, self.new_comment_content)

        self._comments = [*self._comments, comment.to_dto()]
        self.new_comment_content = RichText().to_dto()
        self.is_posting_comment = False

    @rx.event
    def start_edit_comment(self, comment_id: str, content: RichTextDTO):
        """Enter edit mode for a comment.

        :param comment_id: The ID of the comment to edit
        :type comment_id: str
        :param content: The comment's current content
        :type content: RichTextDTO
        """
        self.editing_comment_id = comment_id
        self.edit_comment_content = content

    @rx.event
    def cancel_edit_comment(self):
        """Exit edit mode without saving."""
        self.editing_comment_id = ""

    @rx.event
    def handle_edit_comment_change(self, event_data: dict):
        """Update the draft content of the comment being edited.

        :param event_data: The RichTextDTO data emitted by the rich text editor
        :type event_data: dict
        """
        self.edit_comment_content = RichTextDTO.from_json(event_data)

    @rx.event
    async def save_edit_comment(self):
        """Save the edited comment and exit edit mode."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            updated_comment = TaskCommentService().update_comment(
                self.editing_comment_id, self.edit_comment_content
            )

        updated_dto = updated_comment.to_dto()
        self._comments = [
            updated_dto if comment.id == updated_dto.id else comment for comment in self._comments
        ]
        self.editing_comment_id = ""
