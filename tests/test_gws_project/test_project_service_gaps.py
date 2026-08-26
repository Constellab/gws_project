from datetime import datetime

from gws_core import (
    BadRequestException,
    BaseTestCase,
    CurrentUserService,
    RichText,
    TestMockSpaceService,
    UserGroup,
)
from gws_core import User as GwsCoreUser
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectUserRole, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.project.project_user import ProjectUser
from gws_project.task.task_dto import CreateTaskDTO, TaskPriority
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user import User


# test_project_service_gaps
class TestProjectServiceGaps(BaseTestCase):
    """Test suite for the ProjectService and TaskService public methods that the
    other suites do not cover: the read methods, the role/description updates and
    the project_manager_id branch of update_project."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _get_task_service(self) -> TaskService:
        return TaskService()

    def _create_project(self, name: str) -> Project:
        return self._get_project_service().create_project(
            SaveProjectDTO(
                name=name,
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )

    def _create_user(self, email: str) -> User:
        """Create a user in gws_core and return its synced gws_project counterpart."""
        gws_core_user = GwsCoreUser(
            email=email,
            first_name="Test",
            last_name="User",
            group=UserGroup.USER,
        )
        gws_core_user.save()
        ProjectUserSyncService().sync_all_users()
        return User.get_by_id_and_check(gws_core_user.id)

    def _create_task(
        self,
        project: Project,
        title: str,
        parent_task_id: str | None = None,
        allow_subtasks: bool = False,
    ):
        """Create a task. A task must be created with allow_subtasks=True to be
        able to receive subtasks."""
        task_dto = CreateTaskDTO(
            title=title,
            start_date=datetime(2025, 2, 1),
            due_date=datetime(2025, 2, 10),
            allow_subtasks=allow_subtasks,
        )
        task_service = self._get_task_service()
        if parent_task_id:
            return task_service.create_sub_task(parent_task_id, task_dto)
        return task_service.create_root_task(project.id, task_dto)

    def test_get_project(self):
        """Test get_project returns the project the current user is a member of"""
        project_service = self._get_project_service()
        project = self._create_project("Get Project")

        found = project_service.get_project(project.id)

        self.assertEqual(found.id, project.id)
        self.assertEqual(found.title, "Get Project")

    def test_get_project_users(self):
        """Test get_project_users returns every member of the project"""
        project_service = self._get_project_service()
        current_user = CurrentUserService.get_and_check_current_user()
        project = self._create_project("Get Project Users")

        # Only the owner at first
        project_users = project_service.get_project_users(project.id)
        self.assertEqual(len(project_users), 1)
        self.assertEqual(project_users[0].user.id, current_user.id)
        self.assertEqual(project_users[0].role, ProjectUserRole.OWNER)

        member = self._create_user("member-list@example.com")
        ProjectUser.create_or_update(project=project, user=member, role=ProjectUserRole.USER)

        project_users = project_service.get_project_users(project.id)
        self.assertEqual(len(project_users), 2)
        self.assertEqual(
            {project_user.user.id for project_user in project_users},
            {current_user.id, member.id},
        )

    def test_get_current_user_projects(self):
        """Test get_current_user_projects returns only the projects of the current user"""
        project_service = self._get_project_service()

        count_before = len(project_service.get_current_user_projects())

        project = self._create_project("Current User Project")

        projects = project_service.get_current_user_projects()
        self.assertEqual(len(projects), count_before + 1)
        self.assertIn(project.id, [found.id for found in projects])

    def test_update_project_manager(self):
        """Test update_project sets a new project manager when they are a member"""
        project_service = self._get_project_service()
        project = self._create_project("Manager Project")
        manager = self._create_user("manager-update@example.com")
        ProjectUser.create_or_update(project=project, user=manager, role=ProjectUserRole.USER)

        updated = project_service.update_project(
            project.id,
            SaveProjectDTO(
                name="Manager Project",
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
                project_manager_id=manager.id,
            ),
        )

        self.assertEqual(updated.project_manager.id, manager.id)

    def test_update_project_manager_not_member(self):
        """Test update_project rejects a project manager who is not a member"""
        project_service = self._get_project_service()
        project = self._create_project("Manager Not Member Project")
        outsider = self._create_user("manager-outsider@example.com")

        with self.assertRaises(BadRequestException) as context:
            project_service.update_project(
                project.id,
                SaveProjectDTO(
                    name="Manager Not Member Project",
                    start_date=datetime(2025, 1, 1),
                    due_date=datetime(2025, 12, 31),
                    project_manager_id=outsider.id,
                ),
            )

        self.assertIn("not a member", str(context.exception).lower())

    def test_update_user_role(self):
        """Test update_user_role changes the role of a member"""
        project_service = self._get_project_service()
        project = self._create_project("Update Role Project")
        member = self._create_user("member-role@example.com")
        ProjectUser.create_or_update(project=project, user=member, role=ProjectUserRole.OWNER)

        updated = project_service.update_user_role(project.id, member.id, ProjectUserRole.USER)

        self.assertEqual(updated.role, ProjectUserRole.USER)
        self.assertEqual(
            ProjectUser.get_by_project_and_user(project.id, member.id).role, ProjectUserRole.USER
        )

    def test_update_user_role_not_member(self):
        """Test update_user_role rejects a user who is not a member of the project"""
        project_service = self._get_project_service()
        project = self._create_project("Role Not Member Project")
        outsider = self._create_user("role-outsider@example.com")

        with self.assertRaises(BadRequestException) as context:
            project_service.update_user_role(project.id, outsider.id, ProjectUserRole.USER)

        self.assertIn("not a member", str(context.exception).lower())

    def test_update_user_role_last_owner(self):
        """Test update_user_role refuses to demote the last owner, and allows it
        once another owner exists"""
        project_service = self._get_project_service()
        current_user = CurrentUserService.get_and_check_current_user()
        project = self._create_project("Last Owner Project")

        # The creator is the only owner: demoting them is refused
        with self.assertRaises(BadRequestException) as context:
            project_service.update_user_role(project.id, current_user.id, ProjectUserRole.USER)

        self.assertIn("last owner", str(context.exception).lower())
        self.assertEqual(
            ProjectUser.get_by_project_and_user(project.id, current_user.id).role,
            ProjectUserRole.OWNER,
        )

        # With a second owner, the demotion is allowed
        second_owner = self._create_user("second-owner@example.com")
        ProjectUser.create_or_update(project=project, user=second_owner, role=ProjectUserRole.OWNER)

        updated = project_service.update_user_role(project.id, current_user.id, ProjectUserRole.USER)
        self.assertEqual(updated.role, ProjectUserRole.USER)

    def test_update_project_description(self):
        """Test update_project_description stores the new rich text"""
        project_service = self._get_project_service()
        project = self._create_project("Description Project")

        rich_text = RichText()
        rich_text.add_paragraph("The description of the project.")

        updated = project_service.update_project_description(project.id, rich_text.to_dto())

        self.assert_json(updated.description.to_json_dict(), rich_text.to_dto().to_json_dict())
        self.assert_json(
            project_service.get_project(project.id).description.to_json_dict(),
            rich_text.to_dto().to_json_dict(),
        )

    def test_search_current_user_projects_with_root_tasks(self):
        """Test search_current_user_projects_with_root_tasks returns the projects
        with their root tasks, and applies the title and manager filters"""
        project_service = self._get_project_service()
        current_user = CurrentUserService.get_and_check_current_user()

        project = self._create_project("Searchable Alpha Project")
        self._create_task(project, "Root Task 1")
        root_2 = self._create_task(project, "Root Task 2", allow_subtasks=True)
        # A subtask must not be returned: only root tasks are
        self._create_task(project, "Subtask", parent_task_id=root_2.id)

        results = project_service.search_current_user_projects_with_root_tasks()
        found = next(result for result in results if result.project.id == project.id)
        self.assertEqual(len(found.root_tasks), 2)
        self.assertEqual(
            {task.title for task in found.root_tasks}, {"Root Task 1", "Root Task 2"}
        )

        # Title filter
        results = project_service.search_current_user_projects_with_root_tasks(
            search_title="Searchable Alpha"
        )
        self.assertIn(project.id, [result.project.id for result in results])

        results = project_service.search_current_user_projects_with_root_tasks(
            search_title="No Project Has This Title"
        )
        self.assertEqual(len(results), 0)

        # Manager filter: the creator is the manager of the project
        results = project_service.search_current_user_projects_with_root_tasks(
            manager_id=current_user.id
        )
        self.assertIn(project.id, [result.project.id for result in results])

    def test_get_task(self):
        """Test get_task returns the task"""
        task_service = self._get_task_service()
        project = self._create_project("Get Task Project")
        task = self._create_task(project, "A Task")

        found = task_service.get_task(task.id)

        self.assertEqual(found.id, task.id)
        self.assertEqual(found.title, "A Task")

    def test_get_root_tasks_of_project(self):
        """Test get_root_tasks_of_project returns only the root tasks"""
        task_service = self._get_task_service()
        project = self._create_project("Root Tasks Project")

        self.assertEqual(len(task_service.get_root_tasks_of_project(project.id)), 0)

        root_1 = self._create_task(project, "Root 1")
        root_2 = self._create_task(project, "Root 2", allow_subtasks=True)
        self._create_task(project, "Subtask", parent_task_id=root_2.id)

        root_tasks = task_service.get_root_tasks_of_project(project.id)

        self.assertEqual(len(root_tasks), 2)
        self.assertEqual({task.id for task in root_tasks}, {root_1.id, root_2.id})

    def test_get_subtasks(self):
        """Test get_subtasks returns the direct children of a task only"""
        task_service = self._get_task_service()
        project = self._create_project("Subtasks Project")

        parent = self._create_task(project, "Parent", allow_subtasks=True)
        self.assertEqual(len(task_service.get_subtasks(parent.id)), 0)

        child = self._create_task(project, "Child", parent_task_id=parent.id, allow_subtasks=True)
        # The grandchild must not be returned as a subtask of the parent
        self._create_task(project, "Grandchild", parent_task_id=child.id)

        subtasks = task_service.get_subtasks(parent.id)

        self.assertEqual(len(subtasks), 1)
        self.assertEqual(subtasks[0].id, child.id)

    def test_update_priority(self):
        """Test update_priority sets the priority of a leaf task"""
        task_service = self._get_task_service()
        project = self._create_project("Priority Project")
        task = self._create_task(project, "Leaf Task")

        updated = task_service.update_priority(task.id, TaskPriority.HIGH)

        self.assertEqual(updated.priority, TaskPriority.HIGH)
        self.assertEqual(task_service.get_task(task.id).priority, TaskPriority.HIGH)

        # Setting the same priority again is a no-op
        unchanged = task_service.update_priority(task.id, TaskPriority.HIGH)
        self.assertEqual(unchanged.priority, TaskPriority.HIGH)

    def test_update_priority_propagates_to_parent(self):
        """Test update_priority on a subtask recalculates the parent priority"""
        task_service = self._get_task_service()
        project = self._create_project("Priority Propagation Project")

        parent = self._create_task(project, "Parent", allow_subtasks=True)
        subtask = self._create_task(project, "Subtask", parent_task_id=parent.id)

        task_service.update_priority(subtask.id, TaskPriority.HIGH)

        # The parent inherits the highest priority of its subtasks
        self.assertEqual(task_service.get_task(parent.id).priority, TaskPriority.HIGH)

    def test_update_priority_parent_task_fails(self):
        """Test update_priority refuses a task with subtasks: its priority is computed"""
        task_service = self._get_task_service()
        project = self._create_project("Priority Parent Project")

        parent = self._create_task(project, "Parent", allow_subtasks=True)
        self._create_task(project, "Subtask", parent_task_id=parent.id)

        with self.assertRaises(BadRequestException) as context:
            task_service.update_priority(parent.id, TaskPriority.HIGH)

        self.assertIn("calculated automatically", str(context.exception).lower())

    def test_update_task_description(self):
        """Test update_task_description stores the new rich text"""
        task_service = self._get_task_service()
        project = self._create_project("Task Description Project")
        task = self._create_task(project, "A Task")

        rich_text = RichText()
        rich_text.add_paragraph("The description of the task.")

        updated = task_service.update_task_description(task.id, rich_text.to_dto())

        self.assert_json(updated.description.to_json_dict(), rich_text.to_dto().to_json_dict())
        self.assert_json(
            task_service.get_task(task.id).description.to_json_dict(),
            rich_text.to_dto().to_json_dict(),
        )

    def test_get_descendants_assigned_users(self):
        """Test get_descendants_assigned_users returns the unique users assigned
        to the whole subtree, without duplicates"""
        project_service = self._get_project_service()
        task_service = self._get_task_service()
        project = self._create_project("Descendants Project")

        user_1 = self._create_user("descendant-1@example.com")
        user_2 = self._create_user("descendant-2@example.com")
        project_service.add_user_to_project(project.id, user_1.id, ProjectUserRole.USER)
        project_service.add_user_to_project(project.id, user_2.id, ProjectUserRole.USER)

        parent = self._create_task(project, "Parent", allow_subtasks=True)
        # A task with no subtasks has no assigned descendants
        self.assertEqual(task_service.get_descendants_assigned_users(parent.id), [])

        child_1 = self._create_task(
            project, "Child 1", parent_task_id=parent.id, allow_subtasks=True
        )
        child_2 = self._create_task(project, "Child 2", parent_task_id=parent.id)
        grandchild = self._create_task(project, "Grandchild", parent_task_id=child_1.id)

        task_service.update_assign_to(child_1.id, user_1.id)
        # The same user on two tasks must be returned once
        task_service.update_assign_to(child_2.id, user_1.id)
        task_service.update_assign_to(grandchild.id, user_2.id)

        assigned_users = task_service.get_descendants_assigned_users(parent.id)

        # user_1 (children) and user_2 (grandchild), deduplicated
        self.assertEqual({user.id for user in assigned_users}, {user_1.id, user_2.id})
