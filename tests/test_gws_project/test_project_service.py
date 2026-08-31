from datetime import date, datetime

from gws_core import (
    BadRequestException,
    BaseTestCase,
    CurrentUserService,
    RichText,
    SpaceGroupDTO,
    SpaceGroupType,
    TestMockSpaceService,
    UserGroup,
)
from gws_core.user.user_dto import UserLanguage, UserSpace, UserTheme
from gws_project.project.project import Project
from gws_project.project.project_dto import (
    CreateProjectFromTemplateDTO,
    ProjectUserRole,
    SaveProjectDTO,
)
from gws_project.project.project_service import ProjectService
from gws_project.project.project_user import ProjectUser
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskPriority, TaskStatus
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.task_template import TaskTemplate
from gws_project.user.user import User

from test_gws_project.test_task_service import ProjectUserSyncService


# test_project_service
class TestProjectService(BaseTestCase):
    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_project_service(
        self, group_users: dict[str, list[User]] | None = None
    ) -> ProjectService:
        mock_space_service = TestMockSpaceService()
        if group_users:
            for group_id, users in group_users.items():
                mock_space_service.set_group_users_mock(
                    group_id, [self._to_user_space(user) for user in users]
                )
        return ProjectService(mock_space_service)

    def _to_user_space(self, user: User) -> UserSpace:
        """Build the UserSpace returned by the mocked Space group-users route."""
        return UserSpace(
            id=user.id,
            email=user.email,
            firstname=user.first_name,
            lastname=user.last_name,
            theme=UserTheme.LIGHT_THEME,
            lang=UserLanguage.EN,
            photo=None,
        )

    def test_project(self):
        """Test all public methods of ProjectService in a coherent order"""

        project_service = self._get_project_service()
        current_user = CurrentUserService.get_and_check_current_user()

        # ========== Test 1: create_project ==========
        project_dto = SaveProjectDTO(
            name="Test Project",
            start_date=datetime(2025, 1, 1),
            due_date=datetime(2025, 12, 31),
        )

        project = project_service.create_project(project_dto)

        # Assertions on the created project
        self.assertIsNotNone(project)
        self.assertEqual(project.title, "Test Project")
        self.assertEqual(project.start_date, datetime(2025, 1, 1))
        self.assertEqual(project.due_date, datetime(2025, 12, 31))
        self.assertEqual(project.project_manager.id, current_user.id)

        # Verify that the current user is added as owner
        project_user = ProjectUser.get_by_project_and_user(project.id, current_user.id)
        self.assertEqual(project_user.role, ProjectUserRole.OWNER)

        # ========== Test 2: update_project ==========
        update_dto = SaveProjectDTO(
            name="Updated Project Name",
            start_date=datetime(2025, 2, 1),
            due_date=datetime(2025, 11, 30),
        )

        updated_project = project_service.update_project(project.id, update_dto)

        # Assertions on the updated project
        self.assertEqual(updated_project.id, project.id)
        self.assertEqual(updated_project.title, "Updated Project Name")
        self.assertEqual(updated_project.start_date, datetime(2025, 2, 1))
        self.assertEqual(updated_project.due_date, datetime(2025, 11, 30))

        # ========== Test 3: add_user_to_project ==========
        # Create a second user for testing
        second_user = User(
            email="testuser2@example.com",
            first_name="Test",
            last_name="User2",
            group=UserGroup.USER,
        )
        second_user.save()

        # Manually add user to project for testing (since add_group_to_project requires Space groups)
        project_user = ProjectUser.create_or_update(project=project, user=second_user, role=ProjectUserRole.USER)

        # Assertions on added user
        self.assertIsNotNone(project_user)
        self.assertEqual(project_user.project.id, project.id)
        self.assertEqual(project_user.user.id, second_user.id)
        self.assertEqual(project_user.role, ProjectUserRole.USER)

        # Verify user is in project
        self.assertTrue(ProjectUser.is_user_in_project(project.id, second_user.id))

        # ========== Test 4: remove_user_from_project ==========

        # Try to remove the last owner (should fail)
        with self.assertRaises(BadRequestException) as context:
            project_service.remove_user_from_project(project.id, current_user.id)

        self.assertIn("last owner", str(context.exception).lower())

        # Add second user as owner so we can test removing a user with tasks
        ProjectUser.create_or_update(project=project, user=second_user, role=ProjectUserRole.OWNER)

        # Create a task assigned to the second user
        task = Task()
        task.project = project
        task.title = "Test Task"
        task.description = RichText().to_dto()
        task.start_date = datetime(2025, 3, 1)
        task.due_date = datetime(2025, 3, 15)
        task.status = TaskStatus.TODO
        task.priority = TaskPriority.MEDIUM
        task.assign_to = second_user
        task.save()

        # Try to remove user with assigned tasks (should fail)
        with self.assertRaises(BadRequestException) as context:
            project_service.remove_user_from_project(project.id, second_user.id)

        self.assertIn("task", str(context.exception).lower())

        # Delete the task and try again (should succeed now)
        task.delete_instance()
        project_service.remove_user_from_project(project.id, second_user.id)
        self.assertFalse(ProjectUser.is_user_in_project(project.id, second_user.id))

        # ========== Test 5: delete_project ==========
        # Delete the project using the project ID
        project_service.delete_project(project.id)

        # Verify project is deleted
        project_exists = Project.select().where(Project.id == project.id).exists()
        self.assertFalse(project_exists)

    def test_add_group_to_project(self):
        """Test adding a Space team to a project: the team users are resolved
        via Space, imported into the lab and stored as local ProjectUser rows."""
        current_user = CurrentUserService.get_and_check_current_user()

        member_1 = User(
            email="member1@example.com",
            first_name="Member",
            last_name="One",
            group=UserGroup.USER,
        )
        member_1.save()
        member_2 = User(
            email="member2@example.com",
            first_name="Member",
            last_name="Two",
            group=UserGroup.USER,
        )
        member_2.save()

        project_service = self._get_project_service(
            group_users={"team-group-id": [member_1, member_2]}
        )

        team_group = SpaceGroupDTO(
            id="team-group-id",
            label="Team Group",
            type=SpaceGroupType.TEAM,
            user=None,
        )

        project = project_service.create_project(
            SaveProjectDTO(
                name="Group Project",
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )

        project_users = project_service.add_group_to_project(
            project.id, team_group, ProjectUserRole.OWNER
        )

        # Both group members are added with the requested role
        self.assertEqual(len(project_users), 2)
        self.assertTrue(ProjectUser.is_user_in_project(project.id, member_1.id))
        self.assertTrue(ProjectUser.is_user_in_project(project.id, member_2.id))
        self.assertEqual(
            ProjectUser.get_by_project_and_user(project.id, member_1.id).role,
            ProjectUserRole.OWNER,
        )

        # Re-adding the group with another role does NOT change the role of
        # members who are already in the project: "adding" must never demote
        # an existing member (e.g. strip the last owner of their role).
        project_service.add_group_to_project(project.id, team_group, ProjectUserRole.USER)
        self.assertEqual(
            ProjectUser.get_by_project_and_user(project.id, member_1.id).role,
            ProjectUserRole.OWNER,
        )

        # The owner is untouched
        owner = ProjectUser.get_by_project_and_user(project.id, current_user.id)
        self.assertEqual(owner.role, ProjectUserRole.OWNER)

    def test_add_group_to_project_does_not_remove_last_owner(self):
        """Regression test: adding a team the sole project owner belongs to
        (with role USER) must not strip them of their OWNER role and leave
        the project without any owner."""
        current_user = CurrentUserService.get_and_check_current_user()

        member = User(
            email="teammember@example.com",
            first_name="Team",
            last_name="Member",
            group=UserGroup.USER,
        )
        member.save()

        project_service = self._get_project_service(
            group_users={"team-group-id": [current_user, member]}
        )

        team_group = SpaceGroupDTO(
            id="team-group-id",
            label="Team Group",
            type=SpaceGroupType.TEAM,
            user=None,
        )

        project = project_service.create_project(
            SaveProjectDTO(
                name="Solo Owner Project",
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )

        # The creator is the sole owner of the project
        owner = ProjectUser.get_by_project_and_user(project.id, current_user.id)
        self.assertEqual(owner.role, ProjectUserRole.OWNER)

        # Add a team the owner belongs to, with the default USER role
        project_service.add_group_to_project(project.id, team_group, ProjectUserRole.USER)

        # The owner keeps their OWNER role
        owner = ProjectUser.get_by_project_and_user(project.id, current_user.id)
        self.assertEqual(owner.role, ProjectUserRole.OWNER)
        self.assertEqual(ProjectUser.count_owner_by_project(project.id), 1)

        # The new team member is added with the requested role
        self.assertEqual(
            ProjectUser.get_by_project_and_user(project.id, member.id).role,
            ProjectUserRole.USER,
        )

    def test_add_single_user_group_to_project(self):
        """Test adding a single-user Space group to a project: the user carried
        by the group is added directly, without resolving members via Space."""
        single_user = User(
            email="single@example.com",
            first_name="Single",
            last_name="User",
            group=UserGroup.USER,
        )
        single_user.save()

        # A single-user group carries its user directly and provides no
        # group-users mock: the service must NOT call get_group_users for it.
        project_service = self._get_project_service()

        single_user_group = SpaceGroupDTO(
            id="single-user-group-id",
            label="Single User",
            type=SpaceGroupType.SINGLE_USER,
            user=self._to_user_space(single_user),
        )

        project = project_service.create_project(
            SaveProjectDTO(
                name="Single User Project",
                start_date=datetime(2025, 1, 1),
                due_date=datetime(2025, 12, 31),
            )
        )

        project_users = project_service.add_group_to_project(
            project.id, single_user_group, ProjectUserRole.USER
        )

        # Exactly the single user is added with the requested role
        self.assertEqual(len(project_users), 1)
        self.assertEqual(project_users[0].user.id, single_user.id)
        self.assertTrue(ProjectUser.is_user_in_project(project.id, single_user.id))
        self.assertEqual(
            ProjectUser.get_by_project_and_user(project.id, single_user.id).role,
            ProjectUserRole.USER,
        )

    def test_create_project_with_invalid_dates(self):
        """Test create_project with invalid date range"""
        project_service = self._get_project_service()

        # Test with start date after due date
        invalid_project_dto = SaveProjectDTO(
            name="Invalid Date Project",
            start_date=datetime(2025, 12, 31),
            due_date=datetime(2025, 1, 1),
        )

        with self.assertRaises(BadRequestException) as context:
            project_service.create_project(invalid_project_dto)

        self.assertIn("start date", str(context.exception).lower())
        self.assertIn("due date", str(context.exception).lower())

    def test_create_project_from_template(self):
        """Test creating a project from a template"""
        current_user = CurrentUserService.get_and_check_current_user()

        # Create a project manager user for testing role mapping
        project_manager = User(
            email="manager@example.com",
            first_name="Project",
            last_name="Manager",
            group=UserGroup.USER,
        )
        project_manager.save()

        # Create a developer user for testing role mapping
        developer = User(
            email="developer@example.com",
            first_name="Dev",
            last_name="User",
            group=UserGroup.USER,
        )
        developer.save()
        project_service = self._get_project_service()

        # ========== Create a project template ==========
        rich_text = RichText()
        rich_text.add_paragraph("This is a template for software development projects.")
        template = ProjectTemplate()
        template.name = "Software Development Template"
        template.description = rich_text.to_dto()
        template.save()

        # Create root task template 1: Planning (5 days)
        planning_task = TaskTemplate()
        planning_task.project_template = template
        planning_task.title = "Planning Phase"
        planning_rich_text = RichText()
        planning_rich_text.add_paragraph("Define project scope and requirements")
        planning_task.description = planning_rich_text.to_dto()
        planning_task.start_date_offset = 0  # Starts on day 0
        planning_task.duration_days = 5
        planning_task.priority = TaskPriority.HIGH
        planning_task.allow_subtasks = True
        planning_task.assign_to_role = "project_manager"
        planning_task.save()

        # Create subtask for planning
        planning_subtask = TaskTemplate()
        planning_subtask.project_template = template
        planning_subtask.parent_task = planning_task
        planning_subtask.title = "Requirements Gathering"
        planning_subtask_rich_text = RichText()
        planning_subtask_rich_text.add_paragraph("Gather and document all project requirements")
        planning_subtask.description = planning_subtask_rich_text.to_dto()
        planning_subtask.start_date_offset = 0
        planning_subtask.duration_days = 3
        planning_subtask.priority = TaskPriority.HIGH
        planning_subtask.allow_subtasks = False
        planning_subtask.assign_to_role = "project_manager"
        planning_subtask.save()

        # Create root task template 2: Development (10 days, starts after planning)
        development_task = TaskTemplate()
        development_task.project_template = template
        development_task.title = "Development Phase"
        development_rich_text = RichText()
        development_rich_text.add_paragraph("Implement the project features")
        development_task.description = development_rich_text.to_dto()
        development_task.start_date_offset = 5  # Starts after planning (day 5)
        development_task.duration_days = 10
        development_task.priority = TaskPriority.MEDIUM
        development_task.allow_subtasks = True
        development_task.assign_to_role = "developer"
        development_task.save()

        # Create subtask for development
        dev_subtask = TaskTemplate()
        dev_subtask.project_template = template
        dev_subtask.parent_task = development_task
        dev_subtask.title = "Backend Implementation"
        dev_subtask_rich_text = RichText()
        dev_subtask_rich_text.add_paragraph("Implement backend APIs and database schema")
        dev_subtask.description = dev_subtask_rich_text.to_dto()
        dev_subtask.start_date_offset = 5
        dev_subtask.duration_days = 7
        dev_subtask.priority = TaskPriority.HIGH
        dev_subtask.allow_subtasks = False
        dev_subtask.assign_to_role = "developer"
        dev_subtask.save()

        # ========== Create project from template ==========
        project_dto = CreateProjectFromTemplateDTO(
            name="My New Project",
            start_date=datetime(2025, 1, 1),
            project_manager_id=project_manager.id,
            role_mapping={"project_manager": project_manager.id, "developer": developer.id},
        )

        project = project_service.create_project_from_template(template.id, project_dto)

        # ========== Test assertions ==========
        # Verify project was created correctly
        self.assertIsNotNone(project)
        self.assertEqual(project.title, "My New Project")
        self.assertEqual(project.start_date, datetime(2025, 1, 1))
        # Due date is calculated from template (not from actual created tasks)
        # Max template: dev task at offset 5, duration 10 = 5+10-1 = 14 days total = Jan 15
        self.assertEqual(project.due_date, datetime(2025, 1, 15))
        self.assertEqual(project.project_manager.id, project_manager.id)
        self.assert_json(project.description.to_json_dict(), template.description.to_json_dict())

        # Verify current user is owner
        project_user = ProjectUser.get_by_project_and_user(project.id, current_user.id)
        self.assertEqual(project_user.role, ProjectUserRole.OWNER)

        # Verify users from role_mapping were added to the project
        self.assertTrue(ProjectUser.is_user_in_project(project.id, project_manager.id))
        self.assertTrue(ProjectUser.is_user_in_project(project.id, developer.id))

        # Verify they have USER role
        pm_project_user = ProjectUser.get_by_project_and_user(project.id, project_manager.id)
        self.assertEqual(pm_project_user.role, ProjectUserRole.USER)

        dev_project_user = ProjectUser.get_by_project_and_user(project.id, developer.id)
        self.assertEqual(dev_project_user.role, ProjectUserRole.USER)

        # Verify root tasks were created
        root_tasks = Task.get_root_tasks_of_project(project.id)
        self.assertEqual(len(root_tasks), 2)

        # Find planning and development tasks
        planning_created = next(t for t in root_tasks if t.title == "Planning Phase")
        development_created = next(t for t in root_tasks if t.title == "Development Phase")

        # Verify planning task
        # Note: Parent task dates are calculated from subtasks
        # The subtask is 3 days, so due date will be 1+3-1 = Jan 3
        self.assertEqual(planning_created.start_date, date(2025, 1, 1))
        self.assertEqual(planning_created.due_date, date(2025, 1, 3))
        self.assertEqual(planning_created.priority, TaskPriority.HIGH)
        self.assertEqual(planning_created.allow_subtasks, True)
        # Should be assigned to project_manager via role mapping
        self.assertEqual(planning_created.assign_to.id, project_manager.id)
        # Verify description was copied from template
        self.assert_json(planning_created.description.to_json_dict(), planning_rich_text.to_dto().to_json_dict())

        # Verify development task
        # Note: Parent task dates and priority are calculated from subtasks
        # The subtask starts on day 5 and is 7 days, so 6+(7-1) = Jan 12
        # Priority is inherited from highest subtask priority (HIGH)
        self.assertEqual(development_created.start_date, date(2025, 1, 6))
        self.assertEqual(development_created.due_date, date(2025, 1, 12))
        self.assertEqual(development_created.priority, TaskPriority.HIGH)  # From subtask
        self.assertEqual(development_created.allow_subtasks, True)
        # Should be assigned to developer via role mapping
        self.assertEqual(development_created.assign_to.id, developer.id)
        # Verify description was copied from template
        self.assert_json(development_created.description.to_json_dict(), development_rich_text.to_dto().to_json_dict())

        # Verify subtasks were created
        planning_subtasks = Task.get_subtasks_of_task(planning_created.id)
        self.assertEqual(len(planning_subtasks), 1)
        self.assertEqual(planning_subtasks[0].title, "Requirements Gathering")
        self.assertEqual(planning_subtasks[0].assign_to.id, project_manager.id)
        # Verify subtask description was copied from template
        self.assert_json(
            planning_subtasks[0].description.to_json_dict(), planning_subtask_rich_text.to_dto().to_json_dict()
        )

        development_subtasks = Task.get_subtasks_of_task(development_created.id)
        self.assertEqual(len(development_subtasks), 1)
        self.assertEqual(development_subtasks[0].title, "Backend Implementation")
        self.assertEqual(development_subtasks[0].assign_to.id, developer.id)
        # Verify subtask description was copied from template
        self.assert_json(
            development_subtasks[0].description.to_json_dict(), dev_subtask_rich_text.to_dto().to_json_dict()
        )
