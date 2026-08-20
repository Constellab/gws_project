import re
from datetime import datetime, timedelta

from gws_core import CurrentUserService, RichText

from gws_project.home.home_dto import (
    HomeActivityItemDTO,
    HomeQuickAccessDTO,
    HomeSummaryDTO,
)
from gws_project.my_work.my_work_dto import MyWorkDTO
from gws_project.my_work.my_work_service import MyWorkService
from gws_project.project.project import Project
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task_comment.task_comment import TaskComment
from gws_project.task_history.task_history_event import (
    FEED_TASK_SUBJECT,
    TaskHistoryEvent,
)
from gws_project.user.user import User

# Icon of a comment line in the feed. Change events carry their own icon, from
# TaskHistoryEvent.get_icon().
COMMENT_ICON = "message-square"

# Markdown emphasis and structure markers, stripped from a comment before it is cut down to
# an excerpt: the feed shows one line of plain text, so the syntax would only be noise.
_MARKDOWN_MARKERS = re.compile(r"[*_`~#>\[\]]|!\[|\\")


class HomeService:
    """Service backing the Home screen: where to go next, and what the team has been doing.

    It owns no table and stores nothing. Both halves of the screen are derived on every
    read:

    - the quick-access counts come from `MyWorkService` and `ProjectService`, so Home can
      never disagree with the pages its cards link to,
    - the activity feed comes from `TaskHistoryEvent` and `TaskComment`, the trail the
      Activity tab of a task already writes and reads.

    The feed is a **fixed rolling window** (`ACTIVITY_WINDOW_DAYS`), not a "since your last
    connection" digest. There is deliberately no last-seen marker: nothing is dismissed by
    the mere act of opening the page, opening Home twice in a row shows the same thing, and
    the brick gains no new table to keep in sync. (A marker could not live on `User`
    either - `ProjectUserSyncService` rewrites that row from gws_core on every system
    start, which would wipe it.)

    Like `MyWorkService`, no method here takes a user id: the user is resolved server-side
    from the session, and the feed is bounded to the projects that user is a member of, so
    Home can never widen anyone's reach over the lab's data.
    """

    # How far back the feed looks. A week covers a normal absence (a long weekend, a few
    # days off) without turning the page into an archive - the task's own Activity tab is
    # where the full history lives.
    ACTIVITY_WINDOW_DAYS = 7

    # Hard cap on the feed. A busy team can produce hundreds of events a week, and a Home
    # page is a recap, not a log; when the window holds more, the page says it was clipped
    # rather than implying it showed everything.
    ACTIVITY_MAX_ITEMS = 40

    _COMMENT_EXCERPT_MAX_CHARS = 140

    def get_home_summary(self, now: datetime | None = None) -> HomeSummaryDTO:
        """Build the whole Home screen for the signed-in user.

        :param now: The instant to read the screen at, defaults to the current time. Only
            set by the tests, so that the window and the "today" counts do not drift with
            the clock.
        :type now: datetime | None
        :return: The quick-access counts and the recent activity of the user's colleagues
        :rtype: HomeSummaryDTO
        """
        now = now or datetime.now()
        since = now - timedelta(days=self.ACTIVITY_WINDOW_DAYS)

        user = self._get_current_user()
        projects = ProjectService().get_current_user_projects()
        project_ids = [project.id for project in projects]

        my_work = MyWorkService().get_my_work(now.date())
        items = self._get_recent_activity(user, project_ids, since)

        return HomeSummaryDTO(
            quick_access=self._to_quick_access_dto(my_work, projects),
            # One extra item is fetched to tell a full page from a clipped one, and dropped
            # here so the feed never exceeds the cap it advertises.
            activity_items=items[: self.ACTIVITY_MAX_ITEMS],
            activity_since=since,
            activity_truncated=len(items) > self.ACTIVITY_MAX_ITEMS,
        )

    def _get_current_user(self) -> User:
        """The signed-in user, as the brick's local mirror of the gws_core user.

        Both share the same primary key (see `User.from_gws_core_user`), so the id can be
        carried straight from one to the other.
        """
        core_user = CurrentUserService.get_and_check_current_user()
        return User.get_by_id_and_check(core_user.id)

    def _to_quick_access_dto(
        self, my_work: MyWorkDTO, projects: list[Project]
    ) -> HomeQuickAccessDTO:
        """Reduce the My work screen and the user's projects to the cards' counts."""
        # Counted over both lists and de-duplicated by task: a task can be overdue whether
        # or not it has a slot today, and must not be counted twice when it has one.
        overdue_task_ids = {slot.task_id for slot in my_work.day_slots if slot.is_overdue}
        overdue_task_ids |= {task.task_id for task in my_work.rest_tasks if task.is_overdue}

        project_count = ProjectService().count_current_user_projects()

        return HomeQuickAccessDTO(
            today_slot_count=len(my_work.day_slots),
            today_planned_minutes=my_work.planned_minutes,
            assigned_task_count=len(my_work.rest_tasks),
            overdue_task_count=len(overdue_task_ids),
            ongoing_project_count=project_count.ongoing,
            total_project_count=len(projects),
        )

    def _get_recent_activity(
        self, user: User, project_ids: list[str], since: datetime
    ) -> list[HomeActivityItemDTO]:
        """The colleagues' changes and comments of the window, newest first.

        Three filters make this a *colleagues'* feed rather than a log: the user's own
        projects only, never the user's own actions (they already know what they did), and
        no automatic event - a parent task recalculated from its subtasks is the system
        talking, not a colleague.

        One more item than the cap is returned when the window holds one, so the caller can
        tell a full page from a clipped one.
        """
        if not project_ids:
            # Return early rather than skip the filter: an empty `IN ()` list would widen
            # the query to every task of the lab instead of narrowing it to none.
            return []

        limit = self.ACTIVITY_MAX_ITEMS + 1
        items = self._get_recent_events(user, project_ids, since, limit)
        items += self._get_recent_comments(user, project_ids, since, limit)

        # Newest first. `created_at` only has second precision, so items written within the
        # same second - a status change and the comment explaining it, or a whole cascade of
        # changes from one request - would tie. `sequence` is what resolves them, which is
        # exactly why TaskHistoryEvent carries it; sorting on `created_at` alone here would
        # throw away the ordering the events query established and show a task created after
        # it was moved.
        items.sort(key=lambda item: (item.created_at, item.sequence), reverse=True)

        return items[:limit]

    def _get_recent_events(
        self, user: User, project_ids: list[str], since: datetime, limit: int
    ) -> list[HomeActivityItemDTO]:
        """The task changes of the window, newest first."""
        events = (
            # Task and Project are selected along with the event so that reading the task's
            # title and its project's costs no extra query per row.
            TaskHistoryEvent.select(TaskHistoryEvent, Task, Project)
            .join(Task, on=(TaskHistoryEvent.task == Task.id))
            .join(Project, on=(Task.project == Project.id))
            .where(
                Task.project.in_(project_ids)
                & (TaskHistoryEvent.actor != user.id)
                & ~TaskHistoryEvent.is_automatic
                & (TaskHistoryEvent.created_at >= since)
            )
            # `sequence` breaks the ties `created_at` leaves, as on the task's own timeline.
            .order_by(TaskHistoryEvent.created_at.desc(), TaskHistoryEvent.sequence.desc())
            .limit(limit)
        )
        events = list(events)
        actors = self._get_actors_by_id({event.actor_id for event in events})

        return [
            HomeActivityItemDTO(
                id=event.id,
                kind="event",
                actor=actors[event.actor_id].to_dto(),
                created_at=event.created_at,
                # The feed wording, so a line reads "created the task" under the task's own
                # name rather than the timeline's "created this task".
                message=event.build_message(FEED_TASK_SUBJECT),
                icon=event.get_icon(),
                task_id=event.task.id,
                task_title=event.task.title,
                project_id=event.task.project.id,
                project_title=event.task.project.title,
                sequence=event.sequence,
            )
            for event in events
        ]

    def _get_recent_comments(
        self, user: User, project_ids: list[str], since: datetime, limit: int
    ) -> list[HomeActivityItemDTO]:
        """The comments of the window, newest first, each cut down to a one-line excerpt."""
        comments = (
            TaskComment.select(TaskComment, Task, Project)
            .join(Task, on=(TaskComment.task == Task.id))
            .join(Project, on=(Task.project == Project.id))
            .where(
                Task.project.in_(project_ids)
                & (TaskComment.created_by != user.id)
                & (TaskComment.created_at >= since)
            )
            .order_by(TaskComment.created_at.desc())
            .limit(limit)
        )
        comments = list(comments)
        actors = self._get_actors_by_id({comment.created_by_id for comment in comments})

        return [
            HomeActivityItemDTO(
                id=comment.id,
                kind="comment",
                actor=actors[comment.created_by_id].to_dto(),
                created_at=comment.created_at,
                message=self._build_comment_message(comment),
                icon=COMMENT_ICON,
                task_id=comment.task.id,
                task_title=comment.task.title,
                project_id=comment.task.project.id,
                project_title=comment.task.project.title,
            )
            for comment in comments
        ]

    def _get_actors_by_id(self, user_ids: set[str]) -> dict[str, User]:
        """Load the feed's actors in one query, keyed by id.

        A handful of colleagues account for a whole window of activity, so resolving the
        foreign key row by row would repeat the same few reads dozens of times.
        """
        if not user_ids:
            return {}

        return {user.id: user for user in User.select().where(User.id.in_(list(user_ids)))}

    def _build_comment_message(self, comment: TaskComment) -> str:
        """The feed line for a comment: what was said, cut to one line.

        A comment is rich text; the feed is a single row of plain text, so the excerpt is
        flattened and truncated here. The full comment stays one click away, on the task.
        """
        rich_text = RichText(comment.content)
        if rich_text.is_empty():
            return "commented"

        excerpt = _MARKDOWN_MARKERS.sub("", rich_text.to_markdown())
        excerpt = " ".join(excerpt.split())

        if not excerpt:
            return "commented"
        if len(excerpt) > self._COMMENT_EXCERPT_MAX_CHARS:
            excerpt = excerpt[: self._COMMENT_EXCERPT_MAX_CHARS].rstrip() + "…"

        return f"commented: {excerpt}"
