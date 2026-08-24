from datetime import date, timedelta

import reflex as rx
from gws_core import BaseModelDTO, UserDTO
from gws_project.home.home_dto import HomeActivityItemDTO, HomeSummaryDTO
from gws_project.home.home_service import HomeService
from gws_reflex_main import I18nState, ReflexMainState

from ..common.date_format import format_time, format_weekday_date
from ..common.project_app_router import ProjectAppRouter
from ..common.tasks.task_history_message import HistorySubject, build_history_message
from . import home_translations  # noqa: F401  (side effect: registers translations)


class HomeActivityRowDTO(BaseModelDTO):
    """One line of the activity feed.

    As on the My work screen, every displayed value is a string resolved server-side, so the
    component only ever renders text it is handed.
    """

    id: str  # the underlying event/comment id, used as the foreach list key
    icon: str
    actor: UserDTO
    message: str
    task_id: str
    task_title: str
    project_title: str
    time_text: str  # e.g. "14:32" - the day is carried by the group heading


class HomeActivityGroupDTO(BaseModelDTO):
    """The feed's lines for one day, under a "Today" / "Yesterday" / date heading.

    Grouping by day is what makes a week of activity skimmable, and it lets a line show only
    its time instead of repeating the date on every row.
    """

    day_label: str
    rows: list[HomeActivityRowDTO]


class HomeState(rx.State):
    """State of the Home page: the quick-access cards and the team's recent activity.

    The state holds no query logic - HomeService derives everything - and no user id: the
    service resolves the signed-in user itself, so Home shows one person's projects and one
    person's colleagues.
    """

    my_work_stat: str = ""
    projects_stat: str = ""
    activity_window_label: str = ""
    # Empty unless the window held more activity than the feed's cap, in which case the page
    # says so rather than passing a clipped list off as complete.
    activity_truncated_note: str = ""
    activity_groups: list[HomeActivityGroupDTO] = []

    @rx.var
    def has_activity(self) -> bool:
        return len(self.activity_groups) > 0

    async def on_load(self):
        """Event handler called when the page loads."""
        main_state = await self.get_state(ReflexMainState)
        i18n = await self.get_state(I18nState)

        with await main_state.authenticate_user():
            summary = HomeService().get_home_summary()

        self._apply(summary, i18n)

    @rx.event
    def handle_open_task(self, task_id: str):
        """Open the task detail page, as every other list of the app does."""
        return rx.redirect(ProjectAppRouter.get_task_detail_url(task_id))

    def _apply(self, summary: HomeSummaryDTO, i18n: I18nState) -> None:
        """Turn the service's DTO into the page's pre-formatted vars."""
        self.my_work_stat = self._format_my_work_stat(summary, i18n)
        self.projects_stat = self._format_projects_stat(summary, i18n)
        self.activity_window_label = i18n.tr(
            "home.activity.window", {"days": HomeService.ACTIVITY_WINDOW_DAYS}
        )
        self.activity_truncated_note = (
            i18n.tr(
                "home.activity.truncated", {"count": HomeService.ACTIVITY_MAX_ITEMS}
            )
            if summary.activity_truncated
            else ""
        )
        self.activity_groups = self._group_by_day(summary.activity_items, i18n)

    @staticmethod
    def _format_my_work_stat(summary: HomeSummaryDTO, i18n: I18nState) -> str:
        """The My work card's count line, e.g. "3 scheduled today · 2 overdue"."""
        quick_access = summary.quick_access

        parts = []
        if quick_access.today_slot_count:
            parts.append(
                i18n.tr("home.stat.my_work.today", {"count": quick_access.today_slot_count})
            )
        if quick_access.assigned_task_count:
            parts.append(
                i18n.tr(
                    "home.stat.my_work.assigned", {"count": quick_access.assigned_task_count}
                )
            )
        if quick_access.overdue_task_count:
            parts.append(
                i18n.tr("home.stat.my_work.overdue", {"count": quick_access.overdue_task_count})
            )

        if not parts:
            return i18n.tr("home.stat.my_work.empty")

        return " · ".join(parts)

    @staticmethod
    def _format_projects_stat(summary: HomeSummaryDTO, i18n: I18nState) -> str:
        """The Projects card's count line, e.g. "4 ongoing of 7"."""
        quick_access = summary.quick_access

        if not quick_access.total_project_count:
            return i18n.tr("home.stat.projects.empty")

        return i18n.tr(
            "home.stat.projects",
            {
                "ongoing": quick_access.ongoing_project_count,
                "total": quick_access.total_project_count,
            },
        )

    def _group_by_day(
        self, items: list[HomeActivityItemDTO], i18n: I18nState
    ) -> list[HomeActivityGroupDTO]:
        """Split the feed into consecutive per-day groups.

        The items arrive newest first, so a single pass is enough: a new group starts
        whenever the day changes.
        """
        today = date.today()

        groups: list[HomeActivityGroupDTO] = []
        current_day: date | None = None

        for item in items:
            day = item.created_at.date()
            if day != current_day:
                current_day = day
                groups.append(
                    HomeActivityGroupDTO(
                        day_label=self._format_day_label(day, today, i18n), rows=[]
                    )
                )
            groups[-1].rows.append(self._to_row(item, i18n))

        return groups

    @classmethod
    def _to_row(cls, item: HomeActivityItemDTO, i18n: I18nState) -> HomeActivityRowDTO:
        return HomeActivityRowDTO(
            id=item.id,
            icon=item.icon,
            actor=item.actor,
            message=cls._build_message(item, i18n),
            task_id=item.task_id,
            task_title=item.task_title,
            project_title=item.project_title,
            time_text=format_time(item.created_at),
        )

    @staticmethod
    def _build_message(item: HomeActivityItemDTO, i18n: I18nState) -> str:
        """What the line says, in the reader's language.

        A task change goes through the same builder as the task's own Activity tab, with
        the feed wording, so a line reads "created the task" under the task's own name
        rather than the timeline's "created this task". A comment shows its excerpt, or
        just says that someone commented when it has no text.
        """
        if item.kind == "event" and item.event_type is not None:
            return build_history_message(
                event_type=item.event_type,
                old_value=item.old_value,
                new_value=item.new_value,
                is_automatic=item.is_automatic,
                subject=HistorySubject.FEED,
                i18n=i18n,
            )

        if item.comment_excerpt:
            return i18n.tr(
                "home.activity.commented_with", {"excerpt": item.comment_excerpt}
            )

        return i18n.tr("home.activity.commented")

    @staticmethod
    def _format_day_label(day: date, today: date, i18n: I18nState) -> str:
        """"Today", "Yesterday", or the day as a long date.

        Older days go through common/date_format, so the weekday and month names
        follow the language the user selected.
        """
        if day == today:
            return i18n.tr("home.activity.today")
        if day == today - timedelta(days=1):
            return i18n.tr("home.activity.yesterday")
        return format_weekday_date(day, i18n.lang)
