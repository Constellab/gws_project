from contextlib import contextmanager
from datetime import date, datetime

from gws_core import (
    BadRequestException,
    BaseTestCase,
    CurrentUserService,
    TestMockSpaceService,
    UnauthorizedException,
    UserGroup,
)
from gws_core import User as GwsCoreUser
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import CreateTaskDTO, TaskStatus
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user import User


# test_task_service_move
class TestTaskServiceMove(BaseTestCase):
    """Test suite for TaskService.move_task and TaskService.get_navigable_child_tasks,
    the two methods backing the "move task" feature (moving a task between projects
    and/or reparenting it, browsed through a hierarchical folder-style picker)."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        ProjectUserSyncService().sync_all_users()

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _get_task_service(self) -> TaskService:
        return TaskService()

    def _create_project(
        self, name: str, start_date: date = date(2025, 1, 1), end_date: date = date(2025, 12, 31)
    ) -> Project:
        return self._get_project_service().create_project(
            SaveProjectDTO(
                name=name,
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.min.time()),
            )
        )

    def _create_user(self, email: str) -> tuple[GwsCoreUser, User]:
        """Create a user in the gws_core database and sync it to the gws_project one.

        Both objects are needed: authentication works on the gws_core User, while
        the ProjectUser rows and task assignments reference the gws_project User.
        The sync gives them the same id.
        """
        gws_core_user = GwsCoreUser(
            email=email, first_name="Test", last_name="User", group=UserGroup.USER
        )
        gws_core_user.save()
        ProjectUserSyncService().sync_all_users()
        return gws_core_user, User.get_by_id_and_check(gws_core_user.id)

    @contextmanager
    def _authenticate_as(self, gws_core_user: GwsCoreUser):
        """Run the block with `gws_core_user` as the current user, then restore the previous one."""
        previous_user = CurrentUserService.get_and_check_current_user()
        CurrentUserService.set_auth_user(gws_core_user)
        try:
            yield gws_core_user
        finally:
            CurrentUserService.set_auth_user(previous_user)

    def _create_task(
        self,
        project: Project,
        title: str,
        parent_task_id: str | None = None,
        allow_subtasks: bool = False,
        start_date: date | None = date(2025, 2, 1),
        end_date: date | None = date(2025, 2, 10),
        assign_to_id: str | None = None,
    ) -> Task:
        """Create a task. A task must be created with allow_subtasks=True to be
        able to receive subtasks (used as a "folder" in the move browser)."""
        task_dto = CreateTaskDTO(
            title=title,
            start_date=start_date,
            end_date=end_date,
            allow_subtasks=allow_subtasks,
            assign_to_id=assign_to_id,
        )
        task_service = self._get_task_service()
        if parent_task_id:
            return task_service.create_sub_task(parent_task_id, task_dto)
        return task_service.create_root_task(project.id, task_dto)

    # ------------------------------------------------------------------
    # move_task - moving within the same project
    # ------------------------------------------------------------------

    def test_move_subtask_to_root_same_project(self):
        """A subtask can be promoted to a root task of the same project"""
        task_service = self._get_task_service()
        project = self._create_project("Move Subtask To Root")
        parent = self._create_task(project, "Parent", allow_subtasks=True)
        subtask = self._create_task(project, "Sub", parent_task_id=parent.id)

        moved = task_service.move_task(subtask.id, project.id, None)

        self.assertEqual(moved.project.id, project.id)
        self.assertIsNone(moved.parent_task)
        self.assertTrue(moved.is_root_task())

    def test_move_root_task_to_become_subtask_same_project(self):
        """A root task can be reparented under another task of the same project"""
        task_service = self._get_task_service()
        project = self._create_project("Move Root To Subtask")
        root = self._create_task(project, "Root")
        new_parent = self._create_task(project, "New Parent", allow_subtasks=True)

        moved = task_service.move_task(root.id, project.id, new_parent.id)

        self.assertEqual(moved.project.id, project.id)
        self.assertEqual(moved.parent_task.id, new_parent.id)
        self.assertFalse(moved.is_root_task())

    # ------------------------------------------------------------------
    # move_task - moving across projects
    # ------------------------------------------------------------------

    def test_move_task_to_another_project_moves_whole_subtree(self):
        """Moving a task with subtasks to another project moves all its descendants too"""
        task_service = self._get_task_service()
        project_a = self._create_project("Move Subtree A")
        project_b = self._create_project("Move Subtree B")

        parent = self._create_task(project_a, "Parent", allow_subtasks=True)
        child = self._create_task(project_a, "Child", parent_task_id=parent.id, allow_subtasks=True)
        grandchild = self._create_task(project_a, "Grandchild", parent_task_id=child.id)

        moved = task_service.move_task(parent.id, project_b.id, None)

        self.assertEqual(moved.project.id, project_b.id)
        self.assertEqual(Task.get_by_id(child.id).project.id, project_b.id)
        self.assertEqual(Task.get_by_id(grandchild.id).project.id, project_b.id)

    def test_move_task_under_task_of_another_project(self):
        """A task can be moved under a task belonging to a different project at once"""
        task_service = self._get_task_service()
        project_a = self._create_project("Move Cross Project A")
        project_b = self._create_project("Move Cross Project B")

        task_to_move = self._create_task(project_a, "Move Me")
        destination_parent = self._create_task(project_b, "Destination Parent", allow_subtasks=True)

        moved = task_service.move_task(task_to_move.id, project_b.id, destination_parent.id)

        self.assertEqual(moved.project.id, project_b.id)
        self.assertEqual(moved.parent_task.id, destination_parent.id)

    def test_move_task_to_project_without_access_fails(self):
        """Moving into a project the current user is not a member of is refused"""
        task_service = self._get_task_service()
        project_a = self._create_project("Move No Access A")
        task = self._create_task(project_a, "Task")

        # Create project_b as another user, so the current test user has no access to it
        outsider_gws_core_user, _ = self._create_user("move-outsider-owner@example.com")
        with self._authenticate_as(outsider_gws_core_user):
            project_b = self._create_project("Move No Access B")

        with self.assertRaises(UnauthorizedException):
            task_service.move_task(task.id, project_b.id, None)

    # ------------------------------------------------------------------
    # move_task - cycle prevention
    # ------------------------------------------------------------------

    def test_move_task_under_itself_fails(self):
        """A task cannot be moved under itself"""
        task_service = self._get_task_service()
        project = self._create_project("Move Under Itself")
        task = self._create_task(project, "Task", allow_subtasks=True)

        with self.assertRaises(BadRequestException) as context:
            task_service.move_task(task.id, project.id, task.id)
        self.assertIn("itself", str(context.exception).lower())

    def test_move_task_under_own_descendant_fails(self):
        """A task cannot be moved under one of its own subtasks (would create a cycle)"""
        task_service = self._get_task_service()
        project = self._create_project("Move Under Descendant")
        parent = self._create_task(project, "Parent", allow_subtasks=True)
        child = self._create_task(project, "Child", parent_task_id=parent.id, allow_subtasks=True)

        with self.assertRaises(BadRequestException) as context:
            task_service.move_task(parent.id, project.id, child.id)
        self.assertIn("own subtasks", str(context.exception).lower())

    # ------------------------------------------------------------------
    # move_task - destination validation
    # ------------------------------------------------------------------

    def test_move_task_parent_from_wrong_project_fails(self):
        """The destination parent task must belong to the destination project"""
        task_service = self._get_task_service()
        project_a = self._create_project("Wrong Project Parent A")
        project_b = self._create_project("Wrong Project Parent B")
        task = self._create_task(project_a, "Task")
        parent_in_b = self._create_task(project_b, "Parent In B", allow_subtasks=True)

        with self.assertRaises(BadRequestException) as context:
            task_service.move_task(task.id, project_a.id, parent_in_b.id)
        self.assertIn("destination project", str(context.exception).lower())

    def test_move_task_parent_does_not_allow_subtasks_fails(self):
        """The destination parent task must itself allow subtasks"""
        task_service = self._get_task_service()
        project = self._create_project("Parent No Subtasks")
        task = self._create_task(project, "Task")
        leaf_parent = self._create_task(project, "Leaf Parent", allow_subtasks=False)

        with self.assertRaises(BadRequestException) as context:
            task_service.move_task(task.id, project.id, leaf_parent.id)
        self.assertIn("does not allow subtasks", str(context.exception))

    def test_move_task_noop_fails(self):
        """Moving a task to its current location is refused"""
        task_service = self._get_task_service()
        project = self._create_project("Move Noop")
        root = self._create_task(project, "Root")

        with self.assertRaises(BadRequestException) as context:
            task_service.move_task(root.id, project.id, None)
        self.assertIn("already in that location", str(context.exception).lower())

    # ------------------------------------------------------------------
    # move_task - assignee validation on cross-project moves
    # ------------------------------------------------------------------

    def test_move_task_cross_project_assignee_not_member_fails(self):
        """Moving a task assigned to a user who is not a member of the destination project is refused"""
        task_service = self._get_task_service()
        project_a = self._create_project("Assignee Check A")
        project_b = self._create_project("Assignee Check B")
        _, member = self._create_user("assignee-member@example.com")
        self._get_project_service().add_user_to_project(project_a.id, member.id, ProjectUserRole.USER)

        task = self._create_task(project_a, "Task", assign_to_id=member.id)

        with self.assertRaises(BadRequestException) as context:
            task_service.move_task(task.id, project_b.id, None)
        self.assertIn("not a member", str(context.exception).lower())

    def test_move_task_cross_project_descendant_assignee_not_member_fails(self):
        """Moving a task whose descendant is assigned to a non-member of the destination
        project is refused, even if the moved task itself is fine"""
        task_service = self._get_task_service()
        project_a = self._create_project("Descendant Assignee Check A")
        project_b = self._create_project("Descendant Assignee Check B")
        _, member = self._create_user("descendant-assignee-member@example.com")
        self._get_project_service().add_user_to_project(project_a.id, member.id, ProjectUserRole.USER)

        parent = self._create_task(project_a, "Parent", allow_subtasks=True)
        self._create_task(project_a, "Child", parent_task_id=parent.id, assign_to_id=member.id)

        with self.assertRaises(BadRequestException) as context:
            task_service.move_task(parent.id, project_b.id, None)
        self.assertIn("not a member", str(context.exception).lower())

    def test_move_task_cross_project_assignee_member_of_both_succeeds(self):
        """Moving succeeds when the assignee is a member of both projects"""
        task_service = self._get_task_service()
        project_a = self._create_project("Assignee Both A")
        project_b = self._create_project("Assignee Both B")
        _, member = self._create_user("assignee-both-member@example.com")
        self._get_project_service().add_user_to_project(project_a.id, member.id, ProjectUserRole.USER)
        self._get_project_service().add_user_to_project(project_b.id, member.id, ProjectUserRole.USER)

        task = self._create_task(project_a, "Task", assign_to_id=member.id)

        moved = task_service.move_task(task.id, project_b.id, None)
        self.assertEqual(moved.project.id, project_b.id)

    # ------------------------------------------------------------------
    # move_task - date bounds when a leaf task becomes a root task
    # ------------------------------------------------------------------

    def test_move_leaf_root_task_outside_new_project_bounds_fails(self):
        """A leaf task moved to become a root task must fit the destination project's dates"""
        task_service = self._get_task_service()
        project_a = self._create_project("Date Bounds A")
        project_b = self._create_project(
            "Date Bounds B", start_date=date(2025, 6, 1), end_date=date(2025, 6, 30)
        )
        task = self._create_task(
            project_a, "Task", start_date=date(2025, 2, 1), end_date=date(2025, 2, 10)
        )

        with self.assertRaises(BadRequestException) as context:
            task_service.move_task(task.id, project_b.id, None)
        self.assertIn("start date", str(context.exception).lower())

    def test_move_leaf_root_task_within_new_project_bounds_succeeds(self):
        """A leaf task moved to become a root task succeeds when its dates fit"""
        task_service = self._get_task_service()
        project_a = self._create_project("Date Bounds Ok A")
        project_b = self._create_project(
            "Date Bounds Ok B", start_date=date(2025, 6, 1), end_date=date(2025, 6, 30)
        )
        task = self._create_task(
            project_a, "Task", start_date=date(2025, 6, 5), end_date=date(2025, 6, 10)
        )

        moved = task_service.move_task(task.id, project_b.id, None)
        self.assertEqual(moved.project.id, project_b.id)

    def test_move_leaf_root_task_with_no_dates_skips_date_bounds_check(self):
        """A leaf task with no dates at all has nothing to check against the
        destination project's bounds, so the move succeeds regardless."""
        task_service = self._get_task_service()
        project_a = self._create_project("No Dates Bounds A")
        project_b = self._create_project(
            "No Dates Bounds B", start_date=date(2025, 6, 1), end_date=date(2025, 6, 30)
        )
        task = self._create_task(project_a, "Task", start_date=None, end_date=None)

        moved = task_service.move_task(task.id, project_b.id, None)
        self.assertEqual(moved.project.id, project_b.id)
        self.assertIsNone(moved.start_date)
        self.assertIsNone(moved.end_date)

    def test_move_parent_task_to_root_skips_date_bounds_check(self):
        """A task with subtasks moved to become a root task is NOT date-checked against the
        destination project (its dates are auto-calculated from its subtasks, not manually set)"""
        task_service = self._get_task_service()
        project_a = self._create_project("Parent Date Bounds A")
        project_b = self._create_project(
            "Parent Date Bounds B", start_date=date(2025, 6, 1), end_date=date(2025, 6, 30)
        )
        parent = self._create_task(project_a, "Parent", allow_subtasks=True)
        self._create_task(
            project_a, "Child", parent_task_id=parent.id,
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 10),
        )

        # The parent's auto-calculated dates (Jan) fall outside project_b's bounds (June),
        # but the move must still succeed since parent tasks are exempt from the check.
        moved = task_service.move_task(parent.id, project_b.id, None)
        self.assertEqual(moved.project.id, project_b.id)

    # ------------------------------------------------------------------
    # move_task - ancestor and project progress recalculation
    # ------------------------------------------------------------------

    def test_move_recalculates_old_parent_status(self):
        """Removing a DOING subtask from a parent recalculates the parent's status"""
        task_service = self._get_task_service()
        project = self._create_project("Recalc Old Parent")
        parent = self._create_task(project, "Parent", allow_subtasks=True)
        sub_a = self._create_task(project, "A", parent_task_id=parent.id)
        self._create_task(project, "B", parent_task_id=parent.id)  # stays TODO

        task_service.update_status(sub_a.id, TaskStatus.DOING)
        self.assertEqual(Task.get_by_id(parent.id).status, TaskStatus.DOING)

        # Move sub_a (DOING) out to become a root task: only "B" (TODO) remains under parent
        task_service.move_task(sub_a.id, project.id, None)

        self.assertEqual(Task.get_by_id(parent.id).status, TaskStatus.TODO)

    def test_move_recalculates_new_parent_status(self):
        """Adding a DOING task under a parent recalculates the parent's status"""
        task_service = self._get_task_service()
        project = self._create_project("Recalc New Parent")
        parent = self._create_task(project, "Parent", allow_subtasks=True)
        self._create_task(project, "Existing Child", parent_task_id=parent.id)  # TODO
        self.assertEqual(Task.get_by_id(parent.id).status, TaskStatus.TODO)

        doing_task = self._create_task(project, "Doing Task")
        task_service.update_status(doing_task.id, TaskStatus.DOING)

        task_service.move_task(doing_task.id, project.id, parent.id)

        self.assertEqual(Task.get_by_id(parent.id).status, TaskStatus.DOING)

    def test_move_recalculates_project_progress_on_both_sides(self):
        """Moving a root task between projects updates both projects' progress"""
        task_service = self._get_task_service()
        project_a = self._create_project("Progress A")
        project_b = self._create_project("Progress B")

        # project_a: one DONE (progress 100) + one DOING (progress 0) root task -> average 50.
        # Project progress is only recalculated on a status/priority/allow_subtasks change (or
        # delete), not on task creation, so an explicit status change is needed to trigger it.
        done_root = self._create_task(project_a, "Done Root")
        task_service.update_status(done_root.id, TaskStatus.DONE)
        moving_root = self._create_task(project_a, "Moving Root")
        task_service.update_status(moving_root.id, TaskStatus.DOING)
        self.assertEqual(Project.get_by_id(project_a.id).progress, 50)

        # project_b: one existing DONE root task -> progress 100
        existing_b_root = self._create_task(project_b, "Existing B Root")
        task_service.update_status(existing_b_root.id, TaskStatus.DONE)
        self.assertEqual(Project.get_by_id(project_b.id).progress, 100)

        # Move the still-TODO root task from A to B
        task_service.move_task(moving_root.id, project_b.id, None)

        # project_a now only has the DONE root task left -> progress 100
        self.assertEqual(Project.get_by_id(project_a.id).progress, 100)
        # project_b now averages its existing DONE root and the moved-in TODO root -> 50
        self.assertEqual(Project.get_by_id(project_b.id).progress, 50)

    # ------------------------------------------------------------------
    # get_navigable_child_tasks
    # ------------------------------------------------------------------

    def test_get_navigable_child_tasks_root_level_only_folders(self):
        """Only root tasks that allow subtasks are returned at the project's root level"""
        task_service = self._get_task_service()
        project = self._create_project("Navigable Root Level")
        folder_task = self._create_task(project, "Folder", allow_subtasks=True)
        self._create_task(project, "Leaf", allow_subtasks=False)

        results = task_service.get_navigable_child_tasks(project.id, parent_task_id=None)

        self.assertEqual({task.id for task in results}, {folder_task.id})

    def test_get_navigable_child_tasks_nested_level(self):
        """Only subtasks that allow subtasks are returned under a given parent task"""
        task_service = self._get_task_service()
        project = self._create_project("Navigable Nested Level")
        parent = self._create_task(project, "Parent", allow_subtasks=True)
        sub_folder = self._create_task(
            project, "Sub Folder", parent_task_id=parent.id, allow_subtasks=True
        )
        self._create_task(project, "Sub Leaf", parent_task_id=parent.id, allow_subtasks=False)

        results = task_service.get_navigable_child_tasks(project.id, parent_task_id=parent.id)

        self.assertEqual({task.id for task in results}, {sub_folder.id})

    def test_get_navigable_child_tasks_excludes_self_and_descendants(self):
        """The excluded task and all its descendants are hidden, even when browsing directly
        into the excluded task's own children (deep cycle prevention)"""
        task_service = self._get_task_service()
        project = self._create_project("Navigable Exclusion")
        moved_task = self._create_task(project, "Moved Task", allow_subtasks=True)
        moved_child = self._create_task(
            project, "Moved Child", parent_task_id=moved_task.id, allow_subtasks=True
        )
        other_folder = self._create_task(project, "Other Folder", allow_subtasks=True)

        root_results = task_service.get_navigable_child_tasks(
            project.id, parent_task_id=None, exclude_task_id=moved_task.id
        )
        self.assertNotIn(moved_task.id, {task.id for task in root_results})
        self.assertIn(other_folder.id, {task.id for task in root_results})

        # Even querying inside the excluded task's own subtree, its descendant is hidden
        nested_results = task_service.get_navigable_child_tasks(
            project.id, parent_task_id=moved_task.id, exclude_task_id=moved_task.id
        )
        self.assertNotIn(moved_child.id, {task.id for task in nested_results})

    def test_get_navigable_child_tasks_parent_from_wrong_project_fails(self):
        """The given parent task must belong to the given project"""
        task_service = self._get_task_service()
        project_a = self._create_project("Navigable Wrong Project A")
        project_b = self._create_project("Navigable Wrong Project B")
        parent_in_b = self._create_task(project_b, "Parent In B", allow_subtasks=True)

        with self.assertRaises(BadRequestException) as context:
            task_service.get_navigable_child_tasks(project_a.id, parent_task_id=parent_in_b.id)
        self.assertIn("does not belong", str(context.exception).lower())
