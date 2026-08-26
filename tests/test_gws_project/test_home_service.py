from contextlib import contextmanager
from datetime import date, datetime, timedelta

from gws_core import (
    BaseTestCase,
    CurrentUserService,
    RichText,
    TestMockSpaceService,
    UserGroup,
)
from gws_core import User as GwsCoreUser
from gws_project.home.home_service import HomeService
from gws_project.planning.planning_slot_dto import CreatePlanningSlotDTO
from gws_project.planning.planning_slot_service import PlanningSlotService
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import (
    CreateTaskDTO,
    TaskPriority,
    TaskStatus,
    UpdateTaskDTO,
)
from gws_project.task.task_service import TaskService
from gws_project.task_comment.task_comment_service import TaskCommentService
from gws_project.task_history.task_history_event import TaskHistoryEvent
from gws_project.task_history.task_history_event_type import TaskHistoryEventType
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_home_service
class TestHomeService(BaseTestCase):
    """Test suite for HomeService, the derived Home screen.

    init_before_test only truncates the DB once per test *class* (not per test method - see
    gws_core's BaseTestCase), so each test creates its own users and project, with emails
    unique to the test, to stay independent of execution order.

    The activity feed is read at the real current time rather than a pinned one: the events
    it reads are written by TaskService as a side effect of the changes these tests make, so
    their timestamps are the clock's, not the tests'.
    """

    def _create_user(self, email: str, group: UserGroup = UserGroup.USER) -> GwsCoreUser:
        gws_core_user = GwsCoreUser(
            email=email,
            first_name="Test",
            last_name=email.split("@")[0],
            group=group,
        )
        gws_core_user.save()
        ProjectUserSyncService().sync_all_users()
        return gws_core_user

    @contextmanager
    def _authenticate_as(self, gws_core_user: GwsCoreUser):
        previous_user = CurrentUserService.get_and_check_current_user()
        CurrentUserService.set_auth_user(gws_core_user)
        try:
            yield gws_core_user
        finally:
            CurrentUserService.set_auth_user(previous_user)

    def _create_project(self, name: str) -> Project:
        """A project spanning a wide range, so task due dates always validate."""
        return ProjectService(TestMockSpaceService()).create_project(
            SaveProjectDTO(
                name=name,
                start_date=datetime(2020, 1, 1),
                due_date=datetime(2030, 12, 31),
            )
        )

    def _create_task(
        self,
        project: Project,
        title: str,
        assign_to_id: str,
        due_date: date | None = None,
        allow_subtasks: bool = False,
    ) -> Task:
        return TaskService().create_root_task(
            project.id,
            CreateTaskDTO(
                title=title,
                start_date=None,
                due_date=due_date,
                assign_to_id=assign_to_id,
                allow_subtasks=allow_subtasks,
            ),
        )

    @staticmethod
    def _backdate_events(task_id: str, days: int) -> None:
        """Push a task's history events `days` into the past.

        The events are written by the service under test's collaborators, so their timestamp
        cannot be injected; rewriting it afterwards is the only way to exercise the window.
        """
        TaskHistoryEvent.update(
            created_at=datetime.now() - timedelta(days=days)
        ).where(TaskHistoryEvent.task == task_id).execute()

    def test_feed_shows_a_colleague_change_and_never_my_own(self):
        """The feed is a recap of the *others*' work: my own actions are not repeated to me."""
        me = self._create_user("homefeedme@test.com")
        colleague = self._create_user("homefeedcolleague@test.com")

        with self._authenticate_as(me):
            project = self._create_project("Feed Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, colleague.id, ProjectUserRole.USER
            )
            my_task = self._create_task(project, "My own task", me.id)

        with self._authenticate_as(colleague):
            their_task = self._create_task(project, "Their task", colleague.id)
            TaskService().update_status(their_task.id, TaskStatus.DOING)

        with self._authenticate_as(me):
            summary = HomeService().get_home_summary()

        # Both of the colleague's actions show up (creation, then status change), and none of
        # mine - even though creating my own task wrote a history event too.
        self.assertEqual({item.task_id for item in summary.activity_items}, {their_task.id})
        self.assertNotIn(my_task.id, [item.task_id for item in summary.activity_items])

        # Newest first. The feed carries what changed, not a sentence: the app builds it
        # in the reader's language (see the app's common/tasks/task_history_message.py).
        self.assertEqual(
            summary.activity_items[0].event_type, TaskHistoryEventType.STATUS_CHANGED
        )
        self.assertEqual(summary.activity_items[0].old_value, TaskStatus.TODO.value)
        self.assertEqual(summary.activity_items[0].new_value, TaskStatus.DOING.value)
        self.assertEqual(
            summary.activity_items[-1].event_type, TaskHistoryEventType.CREATED
        )

        # Each line carries its task and project, so the feed needs no second lookup.
        item = summary.activity_items[0]
        self.assertEqual(item.task_title, "Their task")
        self.assertEqual(item.project_title, "Feed Project")
        self.assertEqual(item.actor.id, colleague.id)
        self.assertEqual(item.kind, "event")
        self.assertFalse(summary.activity_truncated)

    def test_feed_carries_the_values_of_the_change(self):
        """A feed line hands the app what changed, for it to word the sentence."""
        me = self._create_user("homewordingme@test.com")
        colleague = self._create_user("homewordingcolleague@test.com")

        with self._authenticate_as(me):
            project = self._create_project("Wording Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, colleague.id, ProjectUserRole.USER
            )

        with self._authenticate_as(colleague):
            task = self._create_task(project, "Renamed task", colleague.id)
            # Only the title changes: the other fields are resent identical.
            TaskService().update_task(
                task.id,
                UpdateTaskDTO(
                    title="New title",
                    start_date=None,
                    due_date=None,
                    status=TaskStatus.TODO,
                    priority=TaskPriority.MEDIUM,
                ),
            )

        with self._authenticate_as(me):
            summary = HomeService().get_home_summary()

        renamed = next(
            item
            for item in summary.activity_items
            if item.event_type == TaskHistoryEventType.TITLE_CHANGED
        )
        self.assertEqual(renamed.old_value, "Renamed task")
        self.assertEqual(renamed.new_value, "New title")
        # A title is free text: it is stored as the user wrote it, nothing to translate.
        self.assertEqual(renamed.kind, "event")

    def test_automatic_events_are_excluded(self):
        """A parent recalculated from its subtasks is the system talking, not a colleague."""
        me = self._create_user("homeautome@test.com")
        colleague = self._create_user("homeautocolleague@test.com")

        with self._authenticate_as(me):
            project = self._create_project("Automatic Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, colleague.id, ProjectUserRole.USER
            )

        with self._authenticate_as(colleague):
            parent = self._create_task(project, "Parent task", colleague.id, allow_subtasks=True)
            subtask = TaskService().create_sub_task(
                parent.id,
                CreateTaskDTO(
                    title="Subtask",
                    start_date=None,
                    due_date=None,
                    assign_to_id=colleague.id,
                ),
            )
            # Moves the subtask to DOING, which cascades an automatic status event onto the
            # parent.
            TaskService().update_status(subtask.id, TaskStatus.DOING)

        with self._authenticate_as(me):
            summary = HomeService().get_home_summary()

        automatic_events = TaskHistoryEvent.select().where(
            TaskHistoryEvent.is_automatic == True  # noqa: E712
        )
        self.assertGreater(automatic_events.count(), 0, "the cascade must have written one")

        for item in summary.activity_items:
            self.assertFalse(item.is_automatic)

    def test_comments_appear_with_an_excerpt(self):
        """A comment is a feed line too, cut down to one line of plain text."""
        me = self._create_user("homecommentme@test.com")
        colleague = self._create_user("homecommentcolleague@test.com")

        with self._authenticate_as(me):
            project = self._create_project("Comment Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, colleague.id, ProjectUserRole.USER
            )
            task = self._create_task(project, "Commented task", me.id)

        with self._authenticate_as(colleague):
            rich_text = RichText()
            rich_text.add_paragraph("The assay came back clean, moving on.")
            TaskCommentService().create_comment(task.id, rich_text.to_dto())

        with self._authenticate_as(me):
            summary = HomeService().get_home_summary()

        comments = [item for item in summary.activity_items if item.kind == "comment"]
        self.assertEqual(len(comments), 1)
        self.assertEqual(
            comments[0].comment_excerpt, "The assay came back clean, moving on."
        )
        self.assertEqual(comments[0].actor.id, colleague.id)
        self.assertEqual(comments[0].task_title, "Commented task")

    def test_long_comment_is_truncated(self):
        """The feed shows one line; the full comment stays on the task."""
        me = self._create_user("homelongme@test.com")
        colleague = self._create_user("homelongcolleague@test.com")

        with self._authenticate_as(me):
            project = self._create_project("Long Comment Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, colleague.id, ProjectUserRole.USER
            )
            task = self._create_task(project, "Long comment task", me.id)

        with self._authenticate_as(colleague):
            rich_text = RichText()
            rich_text.add_paragraph("word " * 100)
            TaskCommentService().create_comment(task.id, rich_text.to_dto())

        with self._authenticate_as(me):
            summary = HomeService().get_home_summary()

        excerpt = summary.activity_items[0].comment_excerpt
        self.assertTrue(excerpt.endswith("…"))
        self.assertLess(len(excerpt), 200)

    def test_activity_outside_my_projects_is_invisible(self):
        """The feed can never widen anyone's reach: membership bounds it."""
        me = self._create_user("homeoutsideme@test.com")
        stranger = self._create_user("homeoutsidestranger@test.com")

        with self._authenticate_as(stranger):
            other_project = self._create_project("Not My Project")
            self._create_task(other_project, "Not my business", stranger.id)

        with self._authenticate_as(me):
            summary = HomeService().get_home_summary()

        self.assertEqual(summary.activity_items, [])
        # No project at all: the empty feed comes from the membership filter, not from luck.
        self.assertEqual(summary.quick_access.total_project_count, 0)

    def test_only_projects_i_belong_to_are_in_the_feed(self):
        """The membership filter, exercised where it actually bites.

        The same colleague is active in two projects, and only one of them is shared with
        me. The stricter case of the two: a feed that leaked would leak *here*, not on a
        user with no project at all.
        """
        me = self._create_user("homescopedme@test.com")
        colleague = self._create_user("homescopedcolleague@test.com")

        with self._authenticate_as(me):
            shared_project = self._create_project("Shared Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                shared_project.id, colleague.id, ProjectUserRole.USER
            )

        with self._authenticate_as(colleague):
            private_project = self._create_project("Colleague Only Project")

            shared_task = self._create_task(shared_project, "Shared task", colleague.id)
            private_task = self._create_task(private_project, "Private task", colleague.id)

            # Both kinds of activity, in both projects: an event and a comment each, so the
            # filter is checked on the two queries the feed makes, not just the events one.
            TaskService().update_status(shared_task.id, TaskStatus.DOING)
            TaskService().update_status(private_task.id, TaskStatus.DOING)

            for task in (shared_task, private_task):
                rich_text = RichText()
                rich_text.add_paragraph("Progress update.")
                TaskCommentService().create_comment(task.id, rich_text.to_dto())

        with self._authenticate_as(me):
            summary = HomeService().get_home_summary()

        self.assertEqual(
            {item.project_title for item in summary.activity_items}, {"Shared Project"}
        )
        self.assertEqual({item.task_id for item in summary.activity_items}, {shared_task.id})
        # The shared project really was active on both counts, so the assertion above is
        # about the filter and not about an empty feed.
        self.assertEqual({item.kind for item in summary.activity_items}, {"event", "comment"})
        self.assertNotIn(
            "Colleague Only Project", [item.project_title for item in summary.activity_items]
        )

    def test_a_lab_admin_is_scoped_to_their_projects_like_anyone_else(self):
        """Being a lab ADMIN is not a way into the feed of a project you are not in.

        Worth its own test because the two notions are easy to conflate: `User.group`
        (lab-wide ADMIN) is unrelated to `ProjectUser.role` (per-project OWNER/USER), and
        only the latter is what `get_current_user_projects` joins on.
        """
        admin = self._create_user("homeadminme@test.com", group=UserGroup.ADMIN)
        colleague = self._create_user("homeadmincolleague@test.com")

        with self._authenticate_as(colleague):
            outside_project = self._create_project("Project The Admin Is Not In")
            self._create_task(outside_project, "Not the admin's business", colleague.id)

        with self._authenticate_as(admin):
            summary = HomeService().get_home_summary()

        self.assertEqual(summary.activity_items, [])
        self.assertEqual(summary.quick_access.total_project_count, 0)

    def test_a_plain_member_sees_the_feed_like_an_owner(self):
        """Both roles read the feed: USER is enough, OWNER is not required."""
        owner = self._create_user("homeroleowner@test.com")
        member = self._create_user("homerolemember@test.com")
        colleague = self._create_user("homerolecolleague@test.com")

        with self._authenticate_as(owner):
            project = self._create_project("Role Project")
            project_service = ProjectService(TestMockSpaceService())
            project_service.add_user_to_project(project.id, member.id, ProjectUserRole.USER)
            project_service.add_user_to_project(project.id, colleague.id, ProjectUserRole.USER)

        with self._authenticate_as(colleague):
            task = self._create_task(project, "Role task", colleague.id)

        with self._authenticate_as(member):
            member_summary = HomeService().get_home_summary()
        with self._authenticate_as(owner):
            owner_summary = HomeService().get_home_summary()

        # The USER-role member is not a second-class reader of their own project.
        self.assertEqual({item.task_id for item in member_summary.activity_items}, {task.id})
        self.assertEqual(
            [item.id for item in member_summary.activity_items],
            [item.id for item in owner_summary.activity_items],
        )

    def test_losing_access_to_a_project_hides_its_past_activity(self):
        """Membership is read at query time, so revoking it closes the feed retroactively."""
        me = self._create_user("homerevokedme@test.com")
        colleague = self._create_user("homerevokedcolleague@test.com")

        with self._authenticate_as(colleague):
            project = self._create_project("Revoked Project")
            project_service = ProjectService(TestMockSpaceService())
            project_service.add_user_to_project(project.id, me.id, ProjectUserRole.USER)
            task = self._create_task(project, "Task I could see", colleague.id)

        with self._authenticate_as(me):
            before = HomeService().get_home_summary()
        self.assertEqual({item.task_id for item in before.activity_items}, {task.id})

        with self._authenticate_as(colleague):
            ProjectService(TestMockSpaceService()).remove_user_from_project(project.id, me.id)

        with self._authenticate_as(me):
            after = HomeService().get_home_summary()

        # The events are untouched in the audit trail; they are simply no longer mine to read.
        self.assertEqual(after.activity_items, [])

    def test_activity_older_than_the_window_is_dropped(self):
        """The feed is a recap of the recent past, not the task's full history."""
        me = self._create_user("homewindowme@test.com")
        colleague = self._create_user("homewindowcolleague@test.com")

        with self._authenticate_as(me):
            project = self._create_project("Window Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, colleague.id, ProjectUserRole.USER
            )

        with self._authenticate_as(colleague):
            old_task = self._create_task(project, "Old news", colleague.id)
            recent_task = self._create_task(project, "Fresh news", colleague.id)

        self._backdate_events(old_task.id, HomeService.ACTIVITY_WINDOW_DAYS + 1)

        with self._authenticate_as(me):
            summary = HomeService().get_home_summary()

        task_ids = {item.task_id for item in summary.activity_items}
        self.assertIn(recent_task.id, task_ids)
        self.assertNotIn(old_task.id, task_ids)

    def test_feed_is_capped_and_says_so(self):
        """Past the cap the page reports a clipped list instead of implying completeness."""
        me = self._create_user("homecapme@test.com")
        colleague = self._create_user("homecapcolleague@test.com")

        with self._authenticate_as(me):
            project = self._create_project("Cap Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, colleague.id, ProjectUserRole.USER
            )

        # One creation event each, so a task count just over the cap overflows the feed.
        with self._authenticate_as(colleague):
            for index in range(HomeService.ACTIVITY_MAX_ITEMS + 2):
                self._create_task(project, f"Task {index}", colleague.id)

        with self._authenticate_as(me):
            summary = HomeService().get_home_summary()

        self.assertEqual(len(summary.activity_items), HomeService.ACTIVITY_MAX_ITEMS)
        self.assertTrue(summary.activity_truncated)

    def test_quick_access_counts_mirror_my_work_and_my_projects(self):
        """The cards' counts are derived, so they can never disagree with their pages."""
        me = self._create_user("homequickme@test.com")
        today = date.today()

        with self._authenticate_as(me):
            project = self._create_project("Quick Access Project")
            scheduled = self._create_task(project, "Scheduled today", me.id)
            self._create_task(project, "Waiting", me.id)
            self._create_task(project, "Late", me.id, due_date=today - timedelta(days=3))

            PlanningSlotService().create_slot(
                CreatePlanningSlotDTO(
                    task_id=scheduled.id,
                    assigned_user_id=me.id,
                    start_datetime=datetime.combine(today, datetime.min.time()).replace(hour=9),
                    end_datetime=datetime.combine(today, datetime.min.time()).replace(hour=10),
                )
            )

            summary = HomeService().get_home_summary()

        quick_access = summary.quick_access
        self.assertEqual(quick_access.today_slot_count, 1)
        self.assertEqual(quick_access.today_planned_minutes, 60)
        # "Waiting" and "Late": the scheduled one is in the day, not behind it.
        self.assertEqual(quick_access.assigned_task_count, 2)
        self.assertEqual(quick_access.overdue_task_count, 1)
        self.assertEqual(quick_access.total_project_count, 1)
