from datetime import datetime

from gws_core import BaseModelDTO, UserDTO


class HomeActivityItemDTO(BaseModelDTO):
    """One line of the Home activity feed: something a colleague did recently.

    Two backend tables feed this shape - `TaskHistoryEvent` (a change on a task) and
    `TaskComment` (a comment posted on one) - flattened into a single object so the feed
    renders one sorted list rather than reconciling two.

    The task and its project are denormalized here rather than looked up by the frontend:
    one line of the feed is one object, as in `MyDaySlotDTO`.
    """

    id: str  # the underlying event/comment id, used as the foreach list key
    kind: str  # "event" or "comment"
    actor: UserDTO
    created_at: datetime
    # Pre-formatted and task-agnostic, e.g. "changed status from To do to Doing". Built by
    # `TaskHistoryEvent.build_message(FEED_TASK_SUBJECT)` for an event, so the feed and the
    # task's own Activity tab never drift apart in wording.
    message: str
    icon: str
    task_id: str
    task_title: str
    project_id: str
    project_title: str
    # Tiebreaker for items sharing a `created_at`, which only has second precision. Events
    # carry `TaskHistoryEvent.sequence`, the global counter written for that very purpose;
    # comments have no equivalent and keep 0, so a comment written in the same second as a
    # change sorts just after it. Arbitrary, but stable from one read to the next.
    sequence: int = 0


class HomeQuickAccessDTO(BaseModelDTO):
    """The live counts shown under the Home quick-access cards.

    Purely indicative: every one of them is already reachable, and shown in full, on the
    page its card links to. Home only says whether it is worth going there.
    """

    today_slot_count: int
    today_planned_minutes: int
    # Tasks assigned to the user with no slot today - "The rest" of the My work screen.
    assigned_task_count: int
    # Tasks of the user past their due date, whether scheduled today or not, counted once.
    overdue_task_count: int
    ongoing_project_count: int
    total_project_count: int


class HomeSummaryDTO(BaseModelDTO):
    """Everything the Home screen shows for one user at one point in time.

    A derived view: it owns no table and stores nothing. In particular there is no
    last-connection marker - the feed is a fixed rolling window, so opening Home twice in a
    row shows the same thing and nothing is ever silently dismissed.
    """

    quick_access: HomeQuickAccessDTO
    # Newest first.
    activity_items: list[HomeActivityItemDTO]
    # Oldest instant the feed covers: what "recent" means on this page.
    activity_since: datetime
    # True when the window held more than the cap and the feed was clipped, so the page can
    # say so instead of presenting a truncated list as complete.
    activity_truncated: bool
