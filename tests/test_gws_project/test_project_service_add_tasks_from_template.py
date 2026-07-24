from datetime import date, datetime

from gws_core import (
    BadRequestException,
    BaseTestCase,
    NotFoundException,
    TestMockSpaceService,
    UserGroup,
)
from gws_core import User as GwsCoreUser
from gws_project.project.project import Project
from gws_project.project.project_dto import AddTasksFromTemplateDTO, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.project_template_dto import SaveProjectTemplateDTO
from gws_project.template.project_template_service import ProjectTemplateService
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_dto import SaveTaskTemplateDTO
from gws_project.template.task_template_service import TaskTemplateService
from gws_project.user.project_user_sync_service import ProjectUserSyncService
from gws_project.user.user import User


# test_project_service_add_tasks_from_template
class TestProjectServiceAddTasksFromTemplate(BaseTestCase):
    """Test suite for ProjectService.add_tasks_from_template: injecting a project
    template's tasks into an already-existing project (as opposed to
    create_project_from_template, which creates a brand new project)."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        ProjectUserSyncService().sync_all_users()

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _get_project_template_service(self) -> ProjectTemplateService:
        return ProjectTemplateService()

    def _get_task_template_service(self) -> TaskTemplateService:
        return TaskTemplateService()

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

    def _create_project_template(self, name: str) -> ProjectTemplate:
        return self._get_project_template_service().create_project_template(
            SaveProjectTemplateDTO(name=name)
        )

    def _create_task_template(
        self,
        template: ProjectTemplate,
        title: str,
        parent_task_id: str | None = None,
        allow_subtasks: bool = False,
        start_date_offset: int = 0,
        duration_days: int = 5,
        assign_to_role: str | None = None,
    ) -> TaskTemplate:
        return self._get_task_template_service().create_task_template(
            template.id,
            SaveTaskTemplateDTO(
                title=title,
                start_date_offset=start_date_offset,
                duration_days=duration_days,
                allow_subtasks=allow_subtasks,
                assign_to_role=assign_to_role,
            ),
            parent_task_id=parent_task_id,
        )

    def _create_user(self, email: str) -> tuple[GwsCoreUser, User]:
        gws_core_user = GwsCoreUser(
            email=email, first_name="Test", last_name="User", group=UserGroup.USER
        )
        gws_core_user.save()
        ProjectUserSyncService().sync_all_users()
        return gws_core_user, User.get_by_id_and_check(gws_core_user.id)

    # ------------------------------------------------------------------

    def test_add_tasks_from_template_creates_root_tasks(self):
        """Each root task template becomes a new root task of the existing project"""
        project_service = self._get_project_service()
        project = self._create_project("Add From Template Basic")
        template = self._create_project_template("Basic Template")
        self._create_task_template(template, "First", start_date_offset=0, duration_days=3)
        self._create_task_template(template, "Second", start_date_offset=5, duration_days=2)

        add_dto = AddTasksFromTemplateDTO(
            project_template_id=template.id, start_date=datetime(2025, 3, 1)
        )
        created = project_service.add_tasks_from_template(project.id, add_dto)

        self.assertEqual(len(created), 2)
        titles = {task.title for task in created}
        self.assertEqual(titles, {"First", "Second"})

        first = next(task for task in created if task.title == "First")
        second = next(task for task in created if task.title == "Second")
        self.assertEqual(first.start_date, date(2025, 3, 1))
        self.assertEqual(first.end_date, date(2025, 3, 3))
        self.assertEqual(second.start_date, date(2025, 3, 6))
        self.assertEqual(second.end_date, date(2025, 3, 7))

        # The tasks now exist as root tasks of the (still same) project
        root_tasks = Task.get_root_tasks_of_project(project.id)
        self.assertEqual({task.title for task in root_tasks}, {"First", "Second"})

    def test_add_tasks_from_template_creates_whole_subtree(self):
        """A root task template with subtasks creates the whole subtree in the project"""
        project_service = self._get_project_service()
        project = self._create_project("Add From Template Subtree")
        template = self._create_project_template("Subtree Template")
        parent = self._create_task_template(
            template, "Parent", allow_subtasks=True, start_date_offset=0, duration_days=10
        )
        self._create_task_template(
            template, "Child", parent_task_id=parent.id, start_date_offset=0, duration_days=3
        )

        add_dto = AddTasksFromTemplateDTO(
            project_template_id=template.id, start_date=datetime(2025, 2, 1)
        )
        created = project_service.add_tasks_from_template(project.id, add_dto)

        self.assertEqual(len(created), 1)
        parent_task = created[0]
        self.assertTrue(parent_task.allow_subtasks)

        subtasks = Task.get_subtasks_of_task(parent_task.id)
        self.assertEqual(len(subtasks), 1)
        self.assertEqual(subtasks[0].title, "Child")

    def test_add_tasks_from_template_uses_given_start_date_not_project_start_date(self):
        """Dates are computed from the given start_date, independent of the project's own dates"""
        project_service = self._get_project_service()
        project = self._create_project(
            "Add From Template Different Dates",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        template = self._create_project_template("Different Dates Template")
        self._create_task_template(template, "Task", start_date_offset=0, duration_days=2)

        # Use a reference date far from the project's own start_date but still within bounds
        add_dto = AddTasksFromTemplateDTO(
            project_template_id=template.id, start_date=datetime(2025, 6, 1)
        )
        created = project_service.add_tasks_from_template(project.id, add_dto)

        self.assertEqual(created[0].start_date, date(2025, 6, 1))
        self.assertEqual(created[0].end_date, date(2025, 6, 2))

    def test_add_tasks_from_template_role_mapping_assigns_users(self):
        """Role-mapped users are assigned to the corresponding tasks and added to the project"""
        project_service = self._get_project_service()
        project = self._create_project("Add From Template Roles")
        template = self._create_project_template("Roles Template")
        self._create_task_template(
            template, "Dev Task", start_date_offset=0, duration_days=3, assign_to_role="developer"
        )
        _, developer = self._create_user("template-developer@example.com")

        add_dto = AddTasksFromTemplateDTO(
            project_template_id=template.id,
            start_date=datetime(2025, 4, 1),
            role_mapping={"developer": developer.id},
        )
        created = project_service.add_tasks_from_template(project.id, add_dto)

        self.assertEqual(created[0].assign_to.id, developer.id)

        # The mapped user was added to the project
        project_users = project_service.get_project_users(project.id)
        self.assertIn(developer.id, {pu.user.id for pu in project_users})

    def test_add_tasks_from_template_no_tasks_fails(self):
        """A template with no root task templates cannot be added"""
        project_service = self._get_project_service()
        project = self._create_project("Add From Template Empty")
        template = self._create_project_template("Empty Template")

        add_dto = AddTasksFromTemplateDTO(project_template_id=template.id, start_date=datetime(2025, 1, 1))

        with self.assertRaises(BadRequestException) as context:
            project_service.add_tasks_from_template(project.id, add_dto)
        self.assertIn("no tasks", str(context.exception).lower())

    def test_add_tasks_from_template_leaf_task_outside_project_bounds_fails(self):
        """A leaf root task whose computed dates fall outside the project's bounds is refused"""
        project_service = self._get_project_service()
        project = self._create_project(
            "Add From Template Bounds", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)
        )
        template = self._create_project_template("Bounds Template")
        self._create_task_template(template, "Task", start_date_offset=0, duration_days=3)

        # This start_date pushes the task's dates past the project's end_date
        add_dto = AddTasksFromTemplateDTO(
            project_template_id=template.id, start_date=datetime(2025, 6, 1)
        )

        with self.assertRaises(BadRequestException):
            project_service.add_tasks_from_template(project.id, add_dto)

    def test_add_tasks_from_template_project_not_found_fails(self):
        """An unknown project ID is refused"""
        project_service = self._get_project_service()
        template = self._create_project_template("Orphan Template")
        self._create_task_template(template, "Task")

        add_dto = AddTasksFromTemplateDTO(project_template_id=template.id, start_date=datetime(2025, 1, 1))

        with self.assertRaises(NotFoundException):
            project_service.add_tasks_from_template("unknown-project-id", add_dto)

    def test_add_tasks_from_template_template_not_found_fails(self):
        """An unknown project template ID is refused"""
        project_service = self._get_project_service()
        project = self._create_project("Add From Template Unknown Template")

        add_dto = AddTasksFromTemplateDTO(
            project_template_id="unknown-template-id", start_date=datetime(2025, 1, 1)
        )

        with self.assertRaises(NotFoundException):
            project_service.add_tasks_from_template(project.id, add_dto)

    def test_add_tasks_from_template_does_not_change_project_dates(self):
        """Adding tasks from a template never changes the existing project's own dates"""
        project_service = self._get_project_service()
        project = self._create_project(
            "Add From Template Keeps Dates", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )
        template = self._create_project_template("Keeps Dates Template")
        self._create_task_template(template, "Task", start_date_offset=0, duration_days=3)

        add_dto = AddTasksFromTemplateDTO(
            project_template_id=template.id, start_date=datetime(2025, 3, 1)
        )
        project_service.add_tasks_from_template(project.id, add_dto)

        refreshed_project = Project.get_by_id(project.id)
        self.assertEqual(refreshed_project.start_date, date(2025, 1, 1))
        self.assertEqual(refreshed_project.end_date, date(2025, 12, 31))
