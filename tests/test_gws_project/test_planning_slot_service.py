from datetime import datetime

from gws_core import (
    BadRequestException,
    BaseTestCase,
    CurrentUserService,
    TestMockSpaceService,
    UserGroup,
)
from gws_project.company.company_dto import SaveCompanyDTO
from gws_project.company.company_service import CompanyService
from gws_project.core.working_hours_settings import WorkingHoursSettings
from gws_project.planning.planning_slot_dto import CreatePlanningSlotDTO, UpdatePlanningSlotDTO
from gws_project.planning.planning_slot_service import PlanningSlotService
from gws_project.project.project import Project
from gws_project.project.project_dto import SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import CreateTaskDTO
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user import User


# test_planning_slot_service
class TestPlanningSlotService(BaseTestCase):
    """Test suite for PlanningSlotService public methods.

    init_before_test only truncates the DB once per test *class* (not per test
    method - see gws_core's BaseTestCase), so every test below uses its own,
    non-overlapping week to stay independent of execution order and of what
    other tests in this class left behind.
    """

    test_user: User

    @classmethod
    def init_before_test(cls):
        super().init_before_test()

        user = User(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            group=UserGroup.USER,
        )
        cls.test_user = user.save()
        ProjectUserSyncService().sync_all_users()

    def _get_service(self) -> PlanningSlotService:
        return PlanningSlotService()

    def _create_test_project(self) -> Project:
        project_service = ProjectService(TestMockSpaceService())
        project_dto = SaveProjectDTO(
            name="Test Project",
            start_date=datetime(2025, 1, 1),
            due_date=datetime(2025, 12, 31),
        )
        return project_service.create_project(project_dto)

    def _create_test_task(self, project: Project, assign_to_id: str | None = None) -> Task:
        current_user = CurrentUserService.get_and_check_current_user()
        task_dto = CreateTaskDTO(
            title="Test Task",
            start_date=None,
            due_date=None,
            assign_to_id=assign_to_id or current_user.id,
        )
        return TaskService().create_root_task(project.id, task_dto)

    def _create_second_user(self) -> User:
        user = User(
            email="second@example.com",
            first_name="Second",
            last_name="User",
            group=UserGroup.USER,
        )
        return user.save()

    def test_create_and_get_slots_for_week(self):
        week_start = datetime(2025, 1, 6)  # Monday, week #1

        service = self._get_service()
        project = self._create_test_project()
        task = self._create_test_task(project)
        current_user = CurrentUserService.get_and_check_current_user()

        slot = service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=11),
            )
        )

        self.assertIsNotNone(slot.id)
        self.assertEqual(slot.task.id, task.id)
        self.assertEqual(slot.assigned_user.id, current_user.id)
        self.assertEqual(slot.duration_minutes(), 120)

        # Within the week
        week_slots = service.get_slots_for_week(week_start.date(), project_id=project.id)
        self.assertEqual(len(week_slots), 1)
        self.assertEqual(week_slots[0].id, slot.id)

        # Not in the following week
        next_week_slots = service.get_slots_for_week(
            (week_start.date().replace(day=13)), project_id=project.id
        )
        self.assertEqual(len(next_week_slots), 0)

    def test_create_slot_invalid_time_range(self):
        week_start = datetime(2025, 1, 20)  # week #2, isolated from other tests

        service = self._get_service()
        project = self._create_test_project()
        task = self._create_test_task(project)
        current_user = CurrentUserService.get_and_check_current_user()

        with self.assertRaises(BadRequestException):
            service.create_slot(
                CreatePlanningSlotDTO(
                    task_id=task.id,
                    assigned_user_id=current_user.id,
                    start_datetime=week_start.replace(hour=11),
                    end_datetime=week_start.replace(hour=9),
                )
            )

    def test_filters_by_project_and_user(self):
        week_start = datetime(2025, 2, 3)  # week #3

        service = self._get_service()
        project_a = self._create_test_project()
        project_b = self._create_test_project()
        current_user = CurrentUserService.get_and_check_current_user()
        second_user = self._create_second_user()

        task_a = self._create_test_task(project_a, assign_to_id=current_user.id)
        task_b = self._create_test_task(project_b, assign_to_id=current_user.id)

        slot_a = service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task_a.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=11),
            )
        )
        slot_b = service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task_b.id,
                assigned_user_id=second_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=11),
            )
        )

        # Project filter
        results = service.get_slots_for_week(week_start.date(), project_id=project_a.id)
        self.assertEqual([r.id for r in results], [slot_a.id])

        # User filter
        results = service.get_slots_for_week(week_start.date(), user_id=second_user.id)
        self.assertEqual([r.id for r in results], [slot_b.id])

        # No filter: both slots (scoped to this test's own week, so no cross-test noise)
        results = service.get_slots_for_week(week_start.date())
        self.assertCountEqual([r.id for r in results], [slot_a.id, slot_b.id])

    def test_filters_by_company(self):
        week_start = datetime(2025, 2, 10)  # week #4

        service = self._get_service()
        project_service = ProjectService(TestMockSpaceService())

        company = CompanyService().create_company(SaveCompanyDTO(name="Acme"))
        project_dto = SaveProjectDTO(
            name="Company Project",
            start_date=datetime(2025, 1, 1),
            due_date=datetime(2025, 12, 31),
            company_id=company.id,
        )
        project_with_company = project_service.create_project(project_dto)
        project_without_company = self._create_test_project()

        current_user = CurrentUserService.get_and_check_current_user()
        task_with_company = self._create_test_task(project_with_company, assign_to_id=current_user.id)
        task_without_company = self._create_test_task(project_without_company, assign_to_id=current_user.id)

        slot_with_company = service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task_with_company.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=11),
            )
        )
        service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task_without_company.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=11),
            )
        )

        results = service.get_slots_for_week(week_start.date(), company_id=company.id)
        self.assertEqual([r.id for r in results], [slot_with_company.id])

    def test_update_slot_move_and_resize(self):
        week_start = datetime(2025, 2, 17)  # week #5

        service = self._get_service()
        project = self._create_test_project()
        task = self._create_test_task(project)
        current_user = CurrentUserService.get_and_check_current_user()
        second_user = self._create_second_user()

        slot = service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=11),
            )
        )

        # Move to another person/day, same duration
        moved = service.update_slot(
            slot.id,
            UpdatePlanningSlotDTO(
                assigned_user_id=second_user.id,
                start_datetime=week_start.replace(day=19, hour=14),
                end_datetime=week_start.replace(day=19, hour=16),
            ),
        )
        self.assertEqual(moved.assigned_user.id, second_user.id)
        self.assertEqual(moved.duration_minutes(), 120)

        # Resize (extend end time)
        resized = service.update_slot(
            slot.id,
            UpdatePlanningSlotDTO(
                assigned_user_id=second_user.id,
                start_datetime=week_start.replace(day=19, hour=14),
                end_datetime=week_start.replace(day=19, hour=17, minute=30),
            ),
        )
        self.assertEqual(resized.duration_minutes(), 210)

    def test_delete_slot(self):
        week_start = datetime(2025, 2, 24)  # week #6

        service = self._get_service()
        project = self._create_test_project()
        task = self._create_test_task(project)
        current_user = CurrentUserService.get_and_check_current_user()

        slot = service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=11),
            )
        )

        service.delete_slot(slot.id)

        self.assertEqual(
            len(service.get_slots_for_week(week_start.date(), project_id=project.id)), 0
        )

    def test_duplicate_week(self):
        source_week_start = datetime(2025, 3, 3)  # week #7
        target_week_start = datetime(2025, 3, 10)

        service = self._get_service()
        project = self._create_test_project()
        task = self._create_test_task(project)
        current_user = CurrentUserService.get_and_check_current_user()

        service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=source_week_start.replace(hour=9),
                end_datetime=source_week_start.replace(hour=11),
            )
        )

        duplicated = service.duplicate_week(source_week_start.date(), target_week_start.date())

        self.assertEqual(len(duplicated), 1)
        # Slots duplicated from a freshly-queried source slot come back timezone-aware
        # (DateTimeUTC.python_value), unlike the naive datetimes built in this test.
        self.assertEqual(
            duplicated[0].start_datetime.replace(tzinfo=None), source_week_start.replace(hour=9, day=10)
        )
        self.assertEqual(
            duplicated[0].end_datetime.replace(tzinfo=None), source_week_start.replace(hour=11, day=10)
        )
        self.assertEqual(duplicated[0].task.id, task.id)
        self.assertEqual(duplicated[0].assigned_user.id, current_user.id)

        # Original week untouched, target week now has the duplicate
        self.assertEqual(
            len(service.get_slots_for_week(source_week_start.date(), project_id=project.id)), 1
        )
        self.assertEqual(
            len(service.get_slots_for_week(target_week_start.date(), project_id=project.id)), 1
        )

    def test_duplicate_week_filtered_by_user(self):
        source_week_start = datetime(2025, 4, 14)  # week #12, isolated from other tests
        target_week_start = datetime(2025, 4, 21)

        service = self._get_service()
        project = self._create_test_project()
        task = self._create_test_task(project)
        current_user = CurrentUserService.get_and_check_current_user()
        second_user = self._create_second_user()

        service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=source_week_start.replace(hour=9),
                end_datetime=source_week_start.replace(hour=11),
            )
        )
        service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=second_user.id,
                start_datetime=source_week_start.replace(hour=9),
                end_datetime=source_week_start.replace(hour=11),
            )
        )

        # Only duplicate the current user's slot, not the second user's
        duplicated = service.duplicate_week(
            source_week_start.date(), target_week_start.date(), user_ids=[current_user.id]
        )

        self.assertEqual(len(duplicated), 1)
        self.assertEqual(duplicated[0].assigned_user.id, current_user.id)
        self.assertEqual(
            len(service.get_slots_for_week(target_week_start.date(), project_id=project.id)), 1
        )

    def test_compute_week_loads(self):
        week_start = datetime(2025, 3, 17)  # week #8

        service = self._get_service()
        project = self._create_test_project()
        task = self._create_test_task(project)
        current_user = CurrentUserService.get_and_check_current_user()
        settings = WorkingHoursSettings.get_or_create_default()

        # 4h on Monday, 5h on Tuesday -> 9h total for the week (under the default 35h
        # weekly capacity, and under the 8h/day capacity: 9h day span - 1h lunch = 8h/day)
        service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=13),
            )
        )
        service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(day=18, hour=9),
                end_datetime=week_start.replace(day=18, hour=14),
            )
        )

        slots = service.get_slots_for_week(week_start.date(), project_id=project.id)
        loads = service.compute_week_loads(slots, [User.get_by_id_and_check(current_user.id)], settings)

        self.assertEqual(len(loads), 1)
        load = loads[0]
        self.assertEqual(load.total_hours, 9.0)
        self.assertEqual(load.capacity_hours, 35.0)
        self.assertFalse(load.is_overloaded)
        self.assertEqual(load.daily_capacity_hours, 8.0)
        self.assertEqual(load.overloaded_dates, [])

    def test_compute_week_loads_with_blank_lunch_time(self):
        # Admin's working-hours form does not enforce non-empty "HH:MM" values, so a
        # blank lunch_start_time (as can happen in practice) must not crash the
        # capacity computation - it should be treated as "no lunch break" instead.
        week_start = datetime(2025, 3, 31)  # week #10

        service = self._get_service()
        project = self._create_test_project()
        task = self._create_test_task(project)
        current_user = CurrentUserService.get_and_check_current_user()

        settings = WorkingHoursSettings.get_or_create_default()
        settings.day_start_time = "09:00"
        settings.day_end_time = "18:00"
        settings.lunch_start_time = ""
        settings.lunch_end_time = "13:00"
        settings.save()

        service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=13),
            )
        )

        slots = service.get_slots_for_week(week_start.date(), project_id=project.id)
        loads = service.compute_week_loads(slots, [User.get_by_id_and_check(current_user.id)], settings)

        self.assertEqual(len(loads), 1)
        # No lunch subtracted: full 9h day span (09:00-18:00) is the daily capacity
        self.assertEqual(loads[0].daily_capacity_hours, 9.0)

    def test_parse_time_to_minutes(self):
        self.assertEqual(PlanningSlotService.parse_time_to_minutes("09:30"), 570)
        self.assertIsNone(PlanningSlotService.parse_time_to_minutes(""))
        self.assertIsNone(PlanningSlotService.parse_time_to_minutes(None))
        self.assertIsNone(PlanningSlotService.parse_time_to_minutes("not-a-time"))

    def test_compute_overlaps(self):
        week_start = datetime(2025, 3, 24)  # week #9

        service = self._get_service()
        project = self._create_test_project()
        task = self._create_test_task(project)
        current_user = CurrentUserService.get_and_check_current_user()

        slot_a = service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=9),
                end_datetime=week_start.replace(hour=12),
            )
        )
        slot_b = service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=11),
                end_datetime=week_start.replace(hour=13),
            )
        )
        # Non-overlapping slot the same day
        service.create_slot(
            CreatePlanningSlotDTO(
                task_id=task.id,
                assigned_user_id=current_user.id,
                start_datetime=week_start.replace(hour=14),
                end_datetime=week_start.replace(hour=15),
            )
        )

        slots = service.get_slots_for_week(week_start.date(), project_id=project.id)
        overlaps = service.compute_overlaps(slots)

        self.assertEqual(len(overlaps), 1)
        self.assertEqual({overlaps[0].slot_a_id, overlaps[0].slot_b_id}, {slot_a.id, slot_b.id})
