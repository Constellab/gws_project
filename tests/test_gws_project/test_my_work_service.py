from contextlib import contextmanager
from datetime import date, datetime, timedelta

from gws_core import (
    BadRequestException,
    BaseTestCase,
    CurrentUserService,
    TestMockSpaceService,
    UserGroup,
)
from gws_core import User as GwsCoreUser
from gws_project.core.working_hours_service import WorkingHoursService
from gws_project.my_work.my_work_service import MyWorkService
from gws_project.planning.planning_slot import PlanningSlot
from gws_project.planning.planning_slot_dto import CreatePlanningSlotDTO
from gws_project.planning.planning_slot_service import PlanningSlotService
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import CreateTaskDTO, TaskPriority, TaskStatus
from gws_project.task.task_service import TaskService
from gws_project.task_history.task_history_event_type import TaskHistoryEventType
from gws_project.task_history.task_history_service import TaskHistoryService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_my_work_service
class TestMyWorkService(BaseTestCase):
    """Test suite for MyWorkService, the derived "My work" view.

    init_before_test only truncates the DB once per test *class* (not per test method - see
    gws_core's BaseTestCase), so each test creates its own users and project, with emails
    unique to the test, to stay independent of execution order.

    Every test pins an explicit `day` rather than relying on today's date, so that overdue /
    upcoming assertions do not drift with the calendar.
    """

    # A Monday, comfortably inside the wide project range created below.
    TEST_DAY = date(2026, 3, 2)

    def _create_user(self, email: str) -> GwsCoreUser:
        gws_core_user = GwsCoreUser(
            email=email,
            first_name="Test",
            last_name=email.split("@")[0],
            group=UserGroup.USER,
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
        """A project spanning a wide range, so task due dates near TEST_DAY always validate."""
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
        priority: TaskPriority = TaskPriority.MEDIUM,
        status: TaskStatus = TaskStatus.TODO,
        allow_subtasks: bool = False,
    ) -> Task:
        return TaskService().create_root_task(
            project.id,
            CreateTaskDTO(
                title=title,
                start_date=None,
                due_date=due_date,
                status=status,
                priority=priority,
                allow_subtasks=allow_subtasks,
                assign_to_id=assign_to_id,
            ),
        )

    def _create_subtask(
        self,
        parent_task: Task,
        title: str,
        assign_to_id: str,
        due_date: date | None = None,
    ) -> Task:
        return TaskService().create_sub_task(
            parent_task.id,
            CreateTaskDTO(
                title=title,
                start_date=None,
                due_date=due_date,
                assign_to_id=assign_to_id,
            ),
        )

    def _create_slot(
        self,
        task: Task,
        user_id: str,
        start: datetime,
        duration_minutes: int = 60,
    ) -> PlanningSlot:
        return PlanningSlotService().create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=user_id,
                start_datetime=start,
                end_datetime=start + timedelta(minutes=duration_minutes),
            )
        )

    @staticmethod
    def _clock(value: datetime) -> str:
        """Wall-clock "HH:MM" of a slot datetime.

        Slot datetimes come back timezone-aware (TypedDateTimeUTC) while the values written
        in these tests are naive, so comparing datetimes directly would raise. The wall clock
        is preserved end to end, so it is what the assertions compare.
        """
        return value.strftime("%H:%M")

    def test_task_scheduled_today_appears_only_in_my_day(self):
        """A task with a slot today is in My day and never repeated in The rest."""
        user = self._create_user("myworkscheduled@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Scheduled Project")
            scheduled = self._create_task(project, "Scheduled task", user.id)
            unscheduled = self._create_task(project, "Unscheduled task", user.id)
            self._create_slot(scheduled, user.id, datetime.combine(self.TEST_DAY, datetime.min.time()).replace(hour=9))

            my_work = MyWorkService().get_my_work(self.TEST_DAY)

        self.assertEqual([slot.task_id for slot in my_work.day_slots], [scheduled.id])
        self.assertEqual([task.task_id for task in my_work.rest_tasks], [unscheduled.id])
        self.assertEqual(my_work.planned_minutes, 60)
        # Default working hours: 09:00-18:00 minus a 12:00-13:00 lunch = 8h.
        self.assertEqual(my_work.daily_capacity_minutes, 480)
        self.assertFalse(my_work.is_over_capacity)

    def test_over_capacity_is_flagged_but_never_blocks(self):
        """Scheduling beyond the daily working hours is reported, not refused."""
        user = self._create_user("myworkoverload@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Overload Project")
            task = self._create_task(project, "Long task", user.id)
            self._create_slot(
                task,
                user.id,
                datetime.combine(self.TEST_DAY, datetime.min.time()).replace(hour=8),
                duration_minutes=9 * 60,
            )

            my_work = MyWorkService().get_my_work(self.TEST_DAY)

        self.assertEqual(my_work.planned_minutes, 9 * 60)
        self.assertTrue(my_work.is_over_capacity)

    def test_backlog_tasks_and_subtasks_of_backlog_parent_are_excluded(self):
        """The backlog is not a commitment, and neither are the children of a backlogged task."""
        user = self._create_user("myworkbacklog@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Backlog Project")

            backlog_task = self._create_task(
                project, "Backlog task", user.id, status=TaskStatus.BACKLOG
            )
            root_task = self._create_task(project, "Root task", user.id)

            backlog_parent = self._create_task(
                project, "Backlog parent", user.id, allow_subtasks=True
            )
            hidden_subtask = self._create_subtask(backlog_parent, "Hidden subtask", user.id)
            # Set the parent's status directly: TaskService.update_status refuses parent tasks
            # (their status is derived), yet this is exactly the DB state the filter must handle.
            backlog_parent.status = TaskStatus.BACKLOG
            backlog_parent.save()

            rest_ids = [task.task_id for task in MyWorkService().get_my_work(self.TEST_DAY).rest_tasks]

        self.assertIn(root_task.id, rest_ids)
        self.assertNotIn(backlog_task.id, rest_ids)
        self.assertNotIn(hidden_subtask.id, rest_ids)

    def test_parent_task_excluded_and_its_subtask_carries_the_parent_title(self):
        """Parent tasks cannot be ticked off, so only their subtasks show, with a breadcrumb."""
        user = self._create_user("myworkparent@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Parent Project")
            parent = self._create_task(project, "Parent task", user.id, allow_subtasks=True)
            subtask = self._create_subtask(parent, "Subtask", user.id)

            rest_tasks = MyWorkService().get_my_work(self.TEST_DAY).rest_tasks

        rest_by_id = {task.task_id: task for task in rest_tasks}
        self.assertNotIn(parent.id, rest_by_id)
        self.assertIn(subtask.id, rest_by_id)
        self.assertEqual(rest_by_id[subtask.id].parent_task_title, "Parent task")

    def test_the_rest_is_sorted_by_overdue_then_due_date_then_priority(self):
        """Overdue first, then due date ascending, undated last, priority as tiebreaker."""
        user = self._create_user("myworksort@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Sort Project")
            undated = self._create_task(project, "Undated", user.id)
            overdue = self._create_task(
                project, "Overdue", user.id, due_date=self.TEST_DAY - timedelta(days=3)
            )
            due_later = self._create_task(
                project, "Due later", user.id, due_date=self.TEST_DAY + timedelta(days=10)
            )
            due_soon_low = self._create_task(
                project,
                "Due soon low",
                user.id,
                due_date=self.TEST_DAY + timedelta(days=2),
                priority=TaskPriority.LOW,
            )
            due_soon_high = self._create_task(
                project,
                "Due soon high",
                user.id,
                due_date=self.TEST_DAY + timedelta(days=2),
                priority=TaskPriority.HIGH,
            )

            rest_tasks = MyWorkService().get_my_work(self.TEST_DAY).rest_tasks

        self.assertEqual(
            [task.task_id for task in rest_tasks],
            [overdue.id, due_soon_high.id, due_soon_low.id, due_later.id, undated.id],
        )
        self.assertTrue(rest_tasks[0].is_overdue)
        self.assertFalse(rest_tasks[1].is_overdue)

    def test_task_scheduled_later_stays_in_the_rest_with_its_next_slot(self):
        """A task planned for another day is annotated, not moved out of The rest."""
        user = self._create_user("myworklater@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Later Project")
            later = self._create_task(project, "Scheduled later", user.id)
            never = self._create_task(project, "Never scheduled", user.id)
            self._create_slot(
                later,
                user.id,
                datetime.combine(self.TEST_DAY + timedelta(days=3), datetime.min.time()).replace(hour=9),
            )

            rest_by_id = {
                task.task_id: task
                for task in MyWorkService().get_my_work(self.TEST_DAY).rest_tasks
            }

        self.assertIsNotNone(rest_by_id[later.id].next_slot_start)
        self.assertEqual(self._clock(rest_by_id[later.id].next_slot_start), "09:00")
        self.assertIsNone(rest_by_id[never.id].next_slot_start)

    def test_slot_scheduled_after_its_due_date_is_flagged(self):
        """A slot posted after the task's own deadline must be visible as such."""
        user = self._create_user("myworkafterdue@test.com")

        with self._authenticate_as(user):
            project = self._create_project("After Due Project")
            task = self._create_task(
                project, "Late task", user.id, due_date=self.TEST_DAY - timedelta(days=1)
            )
            self._create_slot(
                task, user.id, datetime.combine(self.TEST_DAY, datetime.min.time()).replace(hour=9)
            )

            day_slots = MyWorkService().get_my_work(self.TEST_DAY).day_slots

        self.assertEqual(len(day_slots), 1)
        self.assertTrue(day_slots[0].is_overdue)
        self.assertTrue(day_slots[0].is_scheduled_after_due)

    def test_slot_on_someone_elses_task_names_the_assignee(self):
        """A slot of mine on a task owned by someone else must not imply ownership."""
        owner = self._create_user("myworkowner@test.com")
        helper = self._create_user("myworkhelper@test.com")

        with self._authenticate_as(owner):
            project = self._create_project("Shared Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, helper.id, ProjectUserRole.USER
            )
            task = self._create_task(project, "Owner's task", owner.id)
            self._create_slot(
                task, helper.id, datetime.combine(self.TEST_DAY, datetime.min.time()).replace(hour=9)
            )

        with self._authenticate_as(helper):
            my_work = MyWorkService().get_my_work(self.TEST_DAY)

        self.assertEqual(len(my_work.day_slots), 1)
        self.assertEqual(my_work.day_slots[0].other_assignee_name, "Test myworkowner")
        # The task is not assigned to the helper, so it never shows up in their rest list.
        self.assertEqual(my_work.rest_tasks, [])

    def test_reorder_my_day_rewrites_slot_times_and_skips_lunch(self):
        """Reordering compacts the day from its first start time, jumping over lunch."""
        user = self._create_user("myworkreorder@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Reorder Project")
            midnight = datetime.combine(self.TEST_DAY, datetime.min.time())

            task_a = self._create_task(project, "A", user.id)
            task_b = self._create_task(project, "B", user.id)
            task_c = self._create_task(project, "C", user.id)
            slot_a = self._create_slot(task_a, user.id, midnight.replace(hour=9), 120)
            slot_b = self._create_slot(task_b, user.id, midnight.replace(hour=11), 60)
            slot_c = self._create_slot(task_c, user.id, midnight.replace(hour=14), 60)

            my_work = MyWorkService().reorder_my_day(
                [slot_c.id, slot_a.id, slot_b.id], self.TEST_DAY
            )

        # C (1h) from the day's original 09:00 start, A (2h) up to lunch, B pushed past it.
        self.assertEqual(
            [(slot.slot_id, self._clock(slot.start_datetime), self._clock(slot.end_datetime))
             for slot in my_work.day_slots],
            [
                (slot_c.id, "09:00", "10:00"),
                (slot_a.id, "10:00", "12:00"),
                (slot_b.id, "13:00", "14:00"),
            ],
        )
        # Durations and total planned time are preserved by a reordering.
        self.assertEqual(my_work.planned_minutes, 240)

    def test_reorder_my_day_rejects_a_stale_slot_list(self):
        """A list that is not exactly the day's slots is refused rather than half-applied."""
        user = self._create_user("myworkstale@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Stale Project")
            midnight = datetime.combine(self.TEST_DAY, datetime.min.time())
            task_a = self._create_task(project, "A", user.id)
            task_b = self._create_task(project, "B", user.id)
            slot_a = self._create_slot(task_a, user.id, midnight.replace(hour=9), 60)
            self._create_slot(task_b, user.id, midnight.replace(hour=10), 60)

            service = MyWorkService()
            # Missing one of the day's slots.
            with self.assertRaises(BadRequestException):
                service.reorder_my_day([slot_a.id], self.TEST_DAY)
            # Unknown slot id.
            with self.assertRaises(BadRequestException):
                service.reorder_my_day([slot_a.id, "does-not-exist"], self.TEST_DAY)

    def test_find_first_free_start(self):
        """The first opening of the day, lunch and existing slots taken into account."""
        user = self._create_user("myworkfree@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Free Slot Project")
            midnight = datetime.combine(self.TEST_DAY, datetime.min.time())
            settings = WorkingHoursService.get_settings()
            slot_service = PlanningSlotService()

            def first_free(duration_minutes: int):
                return slot_service.find_first_free_start(
                    self.TEST_DAY,
                    duration_minutes,
                    settings,
                    slot_service.get_slots_for_day(self.TEST_DAY, user.id),
                )

            # Empty day: the start of the working day.
            self.assertEqual(self._clock(first_free(120)), "09:00")

            # A morning slot pushes the opening after it.
            task = self._create_task(project, "Morning", user.id)
            self._create_slot(task, user.id, midnight.replace(hour=9), 60)
            self.assertEqual(self._clock(first_free(60)), "10:00")

            # A 3h request no longer fits before lunch (10:00-12:00 is only 2h), so it lands
            # after the break rather than straddling it.
            self.assertEqual(self._clock(first_free(180)), "13:00")

            # Saturate the rest of the day: no opening is proposed at all. Never a time past
            # the end of the working day, which would put the slot outside working hours.
            afternoon = self._create_task(project, "Afternoon", user.id)
            self._create_slot(afternoon, user.id, midnight.replace(hour=10), 8 * 60)
            self.assertIsNone(first_free(120))

    def test_add_to_my_day_creates_a_slot_at_the_first_opening(self):
        """"Add to my day" asks the Planning for a slot; it never picks an arbitrary time."""
        user = self._create_user("myworkadd@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Add Project")
            task = self._create_task(project, "To schedule", user.id)

            slot_dto = MyWorkService().add_to_my_day(task.id, self.TEST_DAY)

            my_work = MyWorkService().get_my_work(self.TEST_DAY)

        self.assertEqual(self._clock(slot_dto.start_datetime), "09:00")
        # Default slot duration, shared with the Planning grid's drag & drop.
        self.assertEqual(slot_dto.duration_minutes, 120)
        # It has moved from The rest into My day.
        self.assertEqual([slot.task_id for slot in my_work.day_slots], [task.id])
        self.assertEqual(my_work.rest_tasks, [])

    def test_add_to_my_day_refuses_a_backlog_or_parent_task(self):
        """The backlog is not a commitment, and a parent task is scheduled through its children."""
        user = self._create_user("myworkaddrefuse@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Add Refuse Project")
            backlog_task = self._create_task(
                project, "Backlog", user.id, status=TaskStatus.BACKLOG
            )
            parent = self._create_task(project, "Parent", user.id, allow_subtasks=True)
            self._create_subtask(parent, "Child", user.id)

            service = MyWorkService()
            with self.assertRaises(BadRequestException):
                service.add_to_my_day(backlog_task.id, self.TEST_DAY)
            with self.assertRaises(BadRequestException):
                service.add_to_my_day(parent.id, self.TEST_DAY)

    def test_add_to_my_day_refuses_once_the_working_day_is_full(self):
        """A full day is rearranged from the Planning, never by appending after hours."""
        user = self._create_user("myworkdayfull@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Day Full Project")
            midnight = datetime.combine(self.TEST_DAY, datetime.min.time())

            # Room left at first.
            self.assertTrue(MyWorkService().get_my_work(self.TEST_DAY).can_add_to_day)

            # Fill the whole working day (09:00-18:00 by default).
            blocker = self._create_task(project, "All day", user.id)
            self._create_slot(blocker, user.id, midnight.replace(hour=9), 9 * 60)

            self.assertFalse(MyWorkService().get_my_work(self.TEST_DAY).can_add_to_day)

            waiting = self._create_task(project, "Waiting", user.id)
            with self.assertRaises(BadRequestException):
                MyWorkService().add_to_my_day(waiting.id, self.TEST_DAY)

            # And nothing was created outside the working hours as a consolation prize.
            day_slots = MyWorkService().get_my_work(self.TEST_DAY).day_slots

        self.assertEqual([slot.task_id for slot in day_slots], [blocker.id])

    def test_complete_task_marks_it_done_and_journals_the_change(self):
        """Ticking a task off delegates to TaskService, which writes the history event."""
        user = self._create_user("myworkcomplete@test.com")

        with self._authenticate_as(user):
            project = self._create_project("Complete Project")
            task = self._create_task(project, "To complete", user.id)

            MyWorkService().complete_task(task.id)

            reloaded = Task.get_by_id_and_check(task.id)
            event_types = [
                event.event_type
                for event in TaskHistoryService().get_events_of_task(task.id)
            ]
            rest_ids = [t.task_id for t in MyWorkService().get_my_work(self.TEST_DAY).rest_tasks]

        self.assertEqual(reloaded.status, TaskStatus.DONE)
        self.assertIn(TaskHistoryEventType.STATUS_CHANGED, event_types)
        self.assertNotIn(task.id, rest_ids)

    def test_complete_task_refuses_someone_elses_task(self):
        """My work only ever acts on my own commitments."""
        owner = self._create_user("myworkcompleteowner@test.com")
        other = self._create_user("myworkcompleteother@test.com")

        with self._authenticate_as(owner):
            project = self._create_project("Complete Refuse Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, other.id, ProjectUserRole.USER
            )
            task = self._create_task(project, "Owner's task", owner.id)

        with self._authenticate_as(other), self.assertRaises(BadRequestException):
            MyWorkService().complete_task(task.id)

    def test_the_view_is_strictly_personal(self):
        """A project member - whatever their role - never sees another member's work here."""
        owner = self._create_user("myworkisolationowner@test.com")
        member = self._create_user("myworkisolationmember@test.com")

        with self._authenticate_as(owner):
            project = self._create_project("Isolation Project")
            ProjectService(TestMockSpaceService()).add_user_to_project(
                project.id, member.id, ProjectUserRole.OWNER
            )
            owner_task = self._create_task(project, "Owner task", owner.id)
            self._create_slot(
                owner_task,
                owner.id,
                datetime.combine(self.TEST_DAY, datetime.min.time()).replace(hour=9),
            )

        # The member shares the project, and is even an OWNER of it.
        with self._authenticate_as(member):
            my_work = MyWorkService().get_my_work(self.TEST_DAY)

        self.assertEqual(my_work.day_slots, [])
        self.assertEqual(my_work.rest_tasks, [])
        self.assertEqual(my_work.planned_minutes, 0)
