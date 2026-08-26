from datetime import date, datetime

from gws_core import BaseTestCase, TestMockSpaceService
from gws_project.project.project import Project
from gws_project.project.project_dto import CreateProjectFromTemplateDTO, SaveProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import CreateTaskDTO, TaskStatus
from gws_project.task.task_service import TaskService
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.project_template_dto import SaveProjectTemplateDTO
from gws_project.template.project_template_service import ProjectTemplateService
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_dto import SaveTaskTemplateDTO
from gws_project.template.task_template_service import TaskTemplateService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_task_ordering
class TestTaskOrdering(BaseTestCase):
    """Test suite for task/task template ordering: tasks (and templates) are primarily
    listed by date, but ties on the same date must fall back to creation/definition
    order rather than an arbitrary order, so that projects created from a template keep
    the tasks in the order they were defined when several share the same date."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        ProjectUserSyncService().sync_all_users()

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _get_task_service(self) -> TaskService:
        return TaskService()

    def _get_project_template_service(self) -> ProjectTemplateService:
        return ProjectTemplateService()

    def _get_task_template_service(self) -> TaskTemplateService:
        return TaskTemplateService()

    def _create_project(
        self, name: str, start_date: date = date(2025, 1, 1), due_date: date = date(2025, 12, 31)
    ) -> Project:
        return self._get_project_service().create_project(
            SaveProjectDTO(
                name=name,
                start_date=datetime.combine(start_date, datetime.min.time()),
                due_date=datetime.combine(due_date, datetime.min.time()),
            )
        )

    def _create_task(
        self,
        project: Project,
        title: str,
        parent_task_id: str | None = None,
        allow_subtasks: bool = False,
        start_date: date | None = date(2025, 2, 1),
        due_date: date | None = date(2025, 2, 10),
    ) -> Task:
        task_dto = CreateTaskDTO(
            title=title, start_date=start_date, due_date=due_date, allow_subtasks=allow_subtasks
        )
        task_service = self._get_task_service()
        if parent_task_id:
            return task_service.create_sub_task(parent_task_id, task_dto)
        return task_service.create_root_task(project.id, task_dto)

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
        start_date_offset: int | None = 0,
        duration_days: int | None = 5,
    ) -> TaskTemplate:
        return self._get_task_template_service().create_task_template(
            template.id,
            SaveTaskTemplateDTO(
                title=title,
                start_date_offset=start_date_offset,
                duration_days=duration_days,
                allow_subtasks=allow_subtasks,
            ),
            parent_task_id=parent_task_id,
        )

    # ------------------------------------------------------------------
    # Task ordering with tied start_date
    # ------------------------------------------------------------------

    def test_root_tasks_with_same_start_date_keep_creation_order(self):
        """Root tasks sharing the same start_date are listed in the order they were created"""
        project = self._create_project("Ordering Root Tasks")
        first = self._create_task(project, "First", start_date=date(2025, 3, 1), due_date=date(2025, 3, 5))
        second = self._create_task(project, "Second", start_date=date(2025, 3, 1), due_date=date(2025, 3, 5))
        third = self._create_task(project, "Third", start_date=date(2025, 3, 1), due_date=date(2025, 3, 5))

        tasks = Task.get_root_tasks_of_project(project.id)

        self.assertEqual([task.id for task in tasks], [first.id, second.id, third.id])

    def test_subtasks_with_same_start_date_keep_creation_order(self):
        """Subtasks sharing the same start_date are listed in the order they were created"""
        project = self._create_project("Ordering Subtasks")
        parent = self._create_task(project, "Parent", allow_subtasks=True)
        first = self._create_task(
            project, "First", parent_task_id=parent.id,
            start_date=date(2025, 3, 1), due_date=date(2025, 3, 5),
        )
        second = self._create_task(
            project, "Second", parent_task_id=parent.id,
            start_date=date(2025, 3, 1), due_date=date(2025, 3, 5),
        )

        subtasks = Task.get_subtasks_of_task(parent.id)

        self.assertEqual([task.id for task in subtasks], [first.id, second.id])

    def test_tasks_with_different_start_dates_still_sorted_by_date(self):
        """Tasks with distinct dates are sorted by date regardless of creation order"""
        project = self._create_project("Ordering By Date")
        later = self._create_task(project, "Later", start_date=date(2025, 6, 1), due_date=date(2025, 6, 5))
        earlier = self._create_task(project, "Earlier", start_date=date(2025, 3, 1), due_date=date(2025, 3, 5))

        tasks = Task.get_root_tasks_of_project(project.id)

        self.assertEqual([task.id for task in tasks], [earlier.id, later.id])

    def test_undated_tasks_are_sorted_last(self):
        """Tasks with no start_date are pushed to the end of the list, after every
        dated task, regardless of creation order"""
        project = self._create_project("Ordering Undated Last")
        undated = self._create_task(project, "Undated", start_date=None, due_date=None)
        dated = self._create_task(
            project, "Dated", start_date=date(2025, 6, 1), due_date=date(2025, 6, 5)
        )

        tasks = Task.get_root_tasks_of_project(project.id)

        self.assertEqual([task.id for task in tasks], [dated.id, undated.id])

    # ------------------------------------------------------------------
    # Task template ordering with tied created_at
    # ------------------------------------------------------------------

    def test_root_task_templates_keep_definition_order(self):
        """Root task templates are listed in the order they were defined, not by created_at
        (which is not precise enough to distinguish templates created in the same second)"""
        template = self._create_project_template("Ordering Templates")
        first = self._create_task_template(template, "First", start_date_offset=0)
        second = self._create_task_template(template, "Second", start_date_offset=0)
        third = self._create_task_template(template, "Third", start_date_offset=0)

        root_templates = TaskTemplate.get_root_tasks_of_template(template.id)

        self.assertEqual([t.id for t in root_templates], [first.id, second.id, third.id])

    def test_subtask_templates_keep_definition_order(self):
        """Subtask templates are listed in the order they were defined"""
        template = self._create_project_template("Ordering Sub Templates")
        parent = self._create_task_template(template, "Parent", allow_subtasks=True)
        first = self._create_task_template(template, "First", parent_task_id=parent.id)
        second = self._create_task_template(template, "Second", parent_task_id=parent.id)

        subtasks = TaskTemplate.get_subtasks_of_template_task(parent.id)

        self.assertEqual([t.id for t in subtasks], [first.id, second.id])

    # ------------------------------------------------------------------
    # End to end: creating a project from a template
    # ------------------------------------------------------------------

    def test_create_project_from_template_keeps_task_order_for_tied_dates(self):
        """Root tasks created from a template with identical date offsets keep the order
        the templates were defined in"""
        template = self._create_project_template("Ordering E2E Root")
        self._create_task_template(template, "First", start_date_offset=0, duration_days=5)
        self._create_task_template(template, "Second", start_date_offset=0, duration_days=5)
        self._create_task_template(template, "Third", start_date_offset=0, duration_days=5)

        project = self._get_project_service().create_project_from_template(
            template.id,
            CreateProjectFromTemplateDTO(name="From Template Root", start_date=datetime(2025, 1, 1)),
        )

        root_tasks = Task.get_root_tasks_of_project(project.id)
        self.assertEqual([task.title for task in root_tasks], ["First", "Second", "Third"])

    def test_create_project_from_template_keeps_subtask_order_for_tied_dates(self):
        """Subtasks created from a template with identical date offsets keep the order
        the templates were defined in"""
        template = self._create_project_template("Ordering E2E Sub")
        parent_template = self._create_task_template(
            template, "Parent", allow_subtasks=True, start_date_offset=0, duration_days=10
        )
        self._create_task_template(
            template, "Sub First", parent_task_id=parent_template.id,
            start_date_offset=0, duration_days=3,
        )
        self._create_task_template(
            template, "Sub Second", parent_task_id=parent_template.id,
            start_date_offset=0, duration_days=3,
        )

        project = self._get_project_service().create_project_from_template(
            template.id,
            CreateProjectFromTemplateDTO(name="From Template Sub", start_date=datetime(2025, 1, 1)),
        )

        root_tasks = Task.get_root_tasks_of_project(project.id)
        self.assertEqual(len(root_tasks), 1)
        subtasks = Task.get_subtasks_of_task(root_tasks[0].id)
        self.assertEqual([task.title for task in subtasks], ["Sub First", "Sub Second"])

    def test_task_templates_with_no_offset_are_sorted_last(self):
        """Task templates with no start_date_offset are pushed to the end of the list,
        after every template that has an offset"""
        template = self._create_project_template("Ordering Templates No Offset")
        no_offset = self._create_task_template(
            template, "No Offset", start_date_offset=None, duration_days=None
        )
        with_offset = self._create_task_template(template, "With Offset", start_date_offset=5)

        root_templates = TaskTemplate.get_root_tasks_of_template(template.id)

        self.assertEqual([t.id for t in root_templates], [with_offset.id, no_offset.id])

    def test_create_project_from_template_with_no_offset_produces_undated_task(self):
        """A task template with no start_date_offset produces a task with no dates at
        all, defaulting to TODO status (there's no date to be "not due yet" against)"""
        template = self._create_project_template("Ordering E2E No Offset")
        self._create_task_template(
            template, "No Offset Task", start_date_offset=None, duration_days=None
        )

        project = self._get_project_service().create_project_from_template(
            template.id,
            CreateProjectFromTemplateDTO(name="From Template No Offset", start_date=datetime(2025, 1, 1)),
        )

        root_tasks = Task.get_root_tasks_of_project(project.id)
        self.assertEqual(len(root_tasks), 1)
        task = root_tasks[0]
        self.assertIsNone(task.start_date)
        self.assertIsNone(task.due_date)
        self.assertEqual(task.status, TaskStatus.TODO)
