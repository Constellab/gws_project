from gws_core import BadRequestException, BaseTestCase, NotFoundException, RichText
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.project_template_dto import SaveProjectTemplateDTO
from gws_project.template.project_template_service import ProjectTemplateService
from gws_project.template.task_template_dto import SaveTaskTemplateDTO
from gws_project.template.task_template_service import TaskTemplateService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_project_template_service
class TestProjectTemplateService(BaseTestCase):
    """Test suite for ProjectTemplateService public methods"""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_service(self) -> ProjectTemplateService:
        return ProjectTemplateService()

    def _create_template(self, name: str) -> ProjectTemplate:
        """Create a template. The name must be unique across the whole test class:
        the database is shared by all the test methods of the class."""
        return self._get_service().create_project_template(SaveProjectTemplateDTO(name=name))

    def test_create_project_template(self):
        """Test create_project_template: a template is created with an empty description"""
        service = self._get_service()

        template = service.create_project_template(SaveProjectTemplateDTO(name="Software Template"))

        self.assertIsNotNone(template.id)
        self.assertEqual(template.name, "Software Template")
        # The description is initialized with an empty rich text
        self.assertIsNotNone(template.description)

    def test_create_project_template_duplicate_name(self):
        """Test create_project_template rejects a duplicate name"""
        service = self._get_service()
        service.create_project_template(SaveProjectTemplateDTO(name="Unique Template"))

        with self.assertRaises(BadRequestException) as context:
            service.create_project_template(SaveProjectTemplateDTO(name="Unique Template"))

        self.assertIn("already exists", str(context.exception).lower())

    def test_get_template(self):
        """Test get_template returns the template, and raises when it does not exist"""
        service = self._get_service()
        template = self._create_template("Get Template")

        found = service.get_template(template.id)
        self.assertEqual(found.id, template.id)
        self.assertEqual(found.name, template.name)

        with self.assertRaises(NotFoundException):
            service.get_template("unknown-template-id")

    def test_get_all_templates(self):
        """Test get_all_templates returns all templates, most recent first"""
        service = self._get_service()

        # The database is shared by all the test methods of the class, count from
        # the existing templates rather than assuming an empty table
        count_before = len(service.get_all_templates())

        first = self._create_template("First Template")
        second = self._create_template("Second Template")

        templates = service.get_all_templates()
        self.assertEqual(len(templates), count_before + 2)

        template_ids = [template.id for template in templates]
        self.assertIn(first.id, template_ids)
        self.assertIn(second.id, template_ids)

    def test_update_project_template(self):
        """Test update_project_template renames a template"""
        service = self._get_service()
        template = self._create_template("Old Name")

        updated = service.update_project_template(template.id, SaveProjectTemplateDTO(name="New Name"))

        self.assertEqual(updated.id, template.id)
        self.assertEqual(updated.name, "New Name")
        self.assertEqual(service.get_template(template.id).name, "New Name")

    def test_update_project_template_same_name(self):
        """Test update_project_template accepts the template's own name (no self conflict)"""
        service = self._get_service()
        template = self._create_template("Stable Name")

        updated = service.update_project_template(template.id, SaveProjectTemplateDTO(name="Stable Name"))

        self.assertEqual(updated.name, "Stable Name")

    def test_update_project_template_duplicate_name(self):
        """Test update_project_template rejects a name used by another template"""
        service = self._get_service()
        self._create_template("Template A")
        template_b = self._create_template("Template B")

        with self.assertRaises(BadRequestException) as context:
            service.update_project_template(template_b.id, SaveProjectTemplateDTO(name="Template A"))

        self.assertIn("already exists", str(context.exception).lower())

    def test_update_project_template_not_found(self):
        """Test update_project_template raises when the template does not exist"""
        service = self._get_service()

        with self.assertRaises(NotFoundException):
            service.update_project_template("unknown-template-id", SaveProjectTemplateDTO(name="Name"))

    def test_delete_project_template(self):
        """Test delete_project_template removes the template and cascades to its task templates"""
        service = self._get_service()
        task_template_service = TaskTemplateService()
        template = self._create_template("Delete Template")

        task_template = task_template_service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Task", duration_days=3)
        )

        service.delete_project_template(template.id)

        self.assertFalse(ProjectTemplate.select().where(ProjectTemplate.id == template.id).exists())
        # The cascade removed the task template as well
        with self.assertRaises(NotFoundException):
            task_template_service.get_task_template(task_template.id)

    def test_update_template_description(self):
        """Test update_template_description stores the new rich text"""
        service = self._get_service()
        template = self._create_template("Description Template")

        rich_text = RichText()
        rich_text.add_paragraph("A template for software projects.")

        updated = service.update_template_description(template.id, rich_text.to_dto())

        self.assert_json(updated.description.to_json_dict(), rich_text.to_dto().to_json_dict())
        # The description is persisted
        self.assert_json(
            service.get_template(template.id).description.to_json_dict(),
            rich_text.to_dto().to_json_dict(),
        )

    def test_get_task_templates_for_template(self):
        """Test get_task_templates_for_template returns only the root task templates"""
        service = self._get_service()
        task_template_service = TaskTemplateService()
        template = self._create_template("Root Tasks Template")

        self.assertEqual(len(service.get_task_templates_for_template(template.id)), 0)

        root = task_template_service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Root", duration_days=5, allow_subtasks=True)
        )
        task_template_service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Subtask", duration_days=2), parent_task_id=root.id
        )

        root_templates = service.get_task_templates_for_template(template.id)

        # The subtask is not returned, only the root
        self.assertEqual(len(root_templates), 1)
        self.assertEqual(root_templates[0].id, root.id)

        with self.assertRaises(NotFoundException):
            service.get_task_templates_for_template("unknown-template-id")

    def test_get_all_roles_for_template(self):
        """Test get_all_roles_for_template returns the distinct assigned roles, sorted"""
        service = self._get_service()
        task_template_service = TaskTemplateService()
        template = self._create_template("Roles Template")

        self.assertEqual(service.get_all_roles_for_template(template.id), [])

        task_template_service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Task 1", assign_to_role="project_manager")
        )
        # Same role twice, must be returned only once
        task_template_service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Task 2", assign_to_role="project_manager")
        )
        task_template_service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Task 3", assign_to_role="developer")
        )
        # Task without role, must be excluded
        task_template_service.create_task_template(template.id, SaveTaskTemplateDTO(title="Task 4"))

        roles = service.get_all_roles_for_template(template.id)

        self.assertEqual(roles, ["developer", "project_manager"])

        with self.assertRaises(NotFoundException):
            service.get_all_roles_for_template("unknown-template-id")
