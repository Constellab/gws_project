from datetime import date, datetime

from gws_core import BaseTestCase, NotFoundException, TestMockSpaceService
from gws_project.company.company import Company
from gws_project.company.company_dto import SaveCompanyDTO
from gws_project.company.company_service import CompanyService
from gws_project.project.project import Project
from gws_project.project.project_dto import SaveProjectDTO
from gws_project.project.project_search_builder import ProjectSearchBuilder
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import CreateTaskDTO
from gws_project.task.task_search_builder import TaskSearchBuilder
from gws_project.task.task_service import TaskService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_project_company_integration
class TestProjectCompanyIntegration(BaseTestCase):
    """Test suite for the optional Project <-> Company link: creating/updating a
    project with a company, and filtering projects/tasks by company."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_project_service(self) -> ProjectService:
        return ProjectService(TestMockSpaceService())

    def _get_task_service(self) -> TaskService:
        return TaskService()

    def _get_company_service(self) -> CompanyService:
        return CompanyService()

    def _create_company(self, name: str) -> Company:
        return self._get_company_service().create_company(SaveCompanyDTO(name=name))

    def _create_project(self, name: str, company_id: str | None = None) -> Project:
        return self._get_project_service().create_project(
            SaveProjectDTO(
                name=name,
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31),
                company_id=company_id,
            )
        )

    def test_create_project_with_company(self):
        """Test that a project created with a company_id is linked to it."""
        company = self._create_company("Client Company")

        project = self._create_project("Project For Client", company_id=company.id)

        self.assertIsNotNone(project.company)
        self.assertEqual(project.company.id, company.id)

        # Re-fetch from the DB: to_dto() calls get_status(), which compares
        # start_date against a plain date - the freshly-created in-memory
        # instance still holds the datetime passed to create_project(), which
        # a DB round-trip normalizes to a date (unrelated to the company link
        # under test here).
        dto = Project.get_by_id_and_check(project.id).to_dto()
        self.assertIsNotNone(dto.company)
        self.assertEqual(dto.company.name, "Client Company")

    def test_create_project_without_company(self):
        """Test that the company link is optional and defaults to None."""
        project = self._create_project("Standalone Project")

        self.assertIsNone(project.company)
        self.assertIsNone(Project.get_by_id_and_check(project.id).to_dto().company)

    def test_create_project_with_unknown_company_id_raises(self):
        """Test that an invalid company_id raises NotFoundException."""
        with self.assertRaises(NotFoundException):
            self._create_project("Doomed Project", company_id="not-a-real-id")

    def test_update_project_sets_company(self):
        """Test that update_project can attach a company to an existing project."""
        project_service = self._get_project_service()
        project = self._create_project("Project To Update")
        company = self._create_company("Newly Linked Company")

        updated = project_service.update_project(
            project.id,
            SaveProjectDTO(
                name=project.title,
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31),
                company_id=company.id,
            ),
        )

        self.assertIsNotNone(updated.company)
        self.assertEqual(updated.company.id, company.id)

    def test_update_project_without_company_id_clears_company(self):
        """update_project always resolves company_id from the DTO: omitting it on
        an update clears a previously-set company (same unconditional-overwrite
        behavior as every other plain field on the project)."""
        project_service = self._get_project_service()
        company = self._create_company("Company To Be Removed")
        project = self._create_project("Project Losing Its Company", company_id=company.id)
        self.assertIsNotNone(project.company)

        updated = project_service.update_project(
            project.id,
            SaveProjectDTO(
                name=project.title,
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31),
            ),
        )

        self.assertIsNone(updated.company)

    def test_project_search_builder_add_company_filter(self):
        """Test that ProjectSearchBuilder.add_company_filter only returns projects
        linked to the given company."""
        company_a = self._create_company("Company A")
        company_b = self._create_company("Company B")
        project_a = self._create_project("Project A", company_id=company_a.id)
        self._create_project("Project B", company_id=company_b.id)
        self._create_project("Project No Company")

        search_builder = ProjectSearchBuilder()
        search_builder.add_company_filter(company_a.id)
        results = search_builder.search_all()

        self.assertEqual({p.id for p in results}, {project_a.id})

    def test_search_current_user_projects_with_root_tasks_company_filter(self):
        """Test the company_id filter of
        ProjectService.search_current_user_projects_with_root_tasks."""
        project_service = self._get_project_service()
        company = self._create_company("Filtered Company")
        project_with_company = self._create_project(
            "Project With Company", company_id=company.id
        )
        self._create_project("Project Without Company")

        results = project_service.search_current_user_projects_with_root_tasks(
            company_id=company.id
        )

        self.assertEqual({result.project.id for result in results}, {project_with_company.id})

    def test_task_search_builder_add_company_filter(self):
        """Test that TaskSearchBuilder.add_company_filter joins through the task's
        project to only return tasks whose project belongs to the given company."""
        task_service = self._get_task_service()
        company = self._create_company("Task Filter Company")
        project_with_company = self._create_project(
            "Project With Company For Tasks", company_id=company.id
        )
        project_without_company = self._create_project("Project Without Company For Tasks")

        task_service.create_root_task(
            project_with_company.id,
            CreateTaskDTO(title="Task In Company Project", start_date=date(2025, 1, 1), end_date=date(2025, 1, 5)),
        )
        task_service.create_root_task(
            project_without_company.id,
            CreateTaskDTO(title="Task In Other Project", start_date=date(2025, 1, 1), end_date=date(2025, 1, 5)),
        )

        search_builder = TaskSearchBuilder()
        search_builder.add_company_filter(company.id)
        results = search_builder.search_all()

        self.assertEqual({task.title for task in results}, {"Task In Company Project"})
