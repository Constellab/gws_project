from gws_core import BadRequestException, BaseTestCase, NotFoundException, RichText
from gws_project.task.task_dto import TaskPriority
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.project_template_dto import SaveProjectTemplateDTO
from gws_project.template.project_template_service import ProjectTemplateService
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_dto import SaveTaskTemplateDTO, UpdateTaskTemplateDTO
from gws_project.template.task_template_service import TaskTemplateService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_task_template_service
class TestTaskTemplateService(BaseTestCase):
    """Test suite for TaskTemplateService public methods"""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        sync_service = ProjectUserSyncService()
        sync_service.sync_all_users()

    def _get_service(self) -> TaskTemplateService:
        return TaskTemplateService()

    def _create_template(self, name: str) -> ProjectTemplate:
        """Create a project template to hold the task templates. The name must be
        unique across the whole test class: the database is shared by all the
        test methods of the class."""
        return ProjectTemplateService().create_project_template(SaveProjectTemplateDTO(name=name))

    def test_create_task_template(self):
        """Test create_task_template creates a root task template with its fields"""
        service = self._get_service()
        template = self._create_template("Create Task Template")

        task_template = service.create_task_template(
            template.id,
            SaveTaskTemplateDTO(
                title="Planning Phase",
                start_date_offset=0,
                duration_days=5,
                priority=TaskPriority.HIGH,
                allow_subtasks=True,
                assign_to_role="project_manager",
            ),
        )

        self.assertIsNotNone(task_template.id)
        self.assertEqual(task_template.project_template.id, template.id)
        self.assertIsNone(task_template.parent_task)
        self.assertEqual(task_template.title, "Planning Phase")
        self.assertEqual(task_template.start_date_offset, 0)
        self.assertEqual(task_template.duration_days, 5)
        self.assertEqual(task_template.priority, TaskPriority.HIGH)
        self.assertTrue(task_template.allow_subtasks)
        self.assertEqual(task_template.assign_to_role, "project_manager")
        # The description is initialized with an empty rich text
        self.assertIsNotNone(task_template.description)

    def test_create_task_template_as_subtask(self):
        """Test create_task_template creates a subtask under a parent that allows subtasks"""
        service = self._get_service()
        template = self._create_template("Create Task Template As Subtask")

        parent = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Parent", duration_days=10, allow_subtasks=True)
        )
        subtask = service.create_task_template(
            template.id,
            SaveTaskTemplateDTO(title="Subtask", start_date_offset=2, duration_days=3),
            parent_task_id=parent.id,
        )

        self.assertEqual(subtask.parent_task.id, parent.id)
        self.assertEqual(subtask.project_template.id, template.id)

        # Unlimited nesting: a subtask that allows subtasks can itself have children
        middle = service.create_task_template(
            template.id,
            SaveTaskTemplateDTO(title="Middle", duration_days=3, allow_subtasks=True),
            parent_task_id=parent.id,
        )
        leaf = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Leaf", duration_days=1), parent_task_id=middle.id
        )

        self.assertEqual(leaf.parent_task.id, middle.id)
        self.assertEqual(leaf.get_depth(), 2)

    def test_create_task_template_template_not_found(self):
        """Test create_task_template raises when the project template does not exist"""
        service = self._get_service()

        with self.assertRaises(NotFoundException):
            service.create_task_template("unknown-template-id", SaveTaskTemplateDTO(title="Task"))

    def test_create_task_template_parent_not_found(self):
        """Test create_task_template raises when the parent task template does not exist"""
        service = self._get_service()
        template = self._create_template("Create Task Template Parent Not Found")

        with self.assertRaises(NotFoundException):
            service.create_task_template(
                template.id, SaveTaskTemplateDTO(title="Task"), parent_task_id="unknown-task-id"
            )

    def test_create_task_template_parent_from_other_template(self):
        """Test create_task_template rejects a parent belonging to another project template"""
        service = self._get_service()
        template_a = self._create_template("Template A")
        template_b = self._create_template("Template B")

        parent_of_a = service.create_task_template(
            template_a.id, SaveTaskTemplateDTO(title="Parent", allow_subtasks=True)
        )

        with self.assertRaises(BadRequestException) as context:
            service.create_task_template(
                template_b.id, SaveTaskTemplateDTO(title="Subtask"), parent_task_id=parent_of_a.id
            )

        self.assertIn("does not belong", str(context.exception).lower())

    def test_create_task_template_parent_disallows_subtasks(self):
        """Test create_task_template rejects a parent that does not allow subtasks"""
        service = self._get_service()
        template = self._create_template("Create Task Template Parent Disallows Subtasks")

        leaf = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Leaf", allow_subtasks=False)
        )

        with self.assertRaises(BadRequestException) as context:
            service.create_task_template(
                template.id, SaveTaskTemplateDTO(title="Subtask"), parent_task_id=leaf.id
            )

        self.assertIn("does not allow subtasks", str(context.exception).lower())

    def test_create_task_template_negative_offset(self):
        """Test create_task_template rejects a negative start date offset"""
        service = self._get_service()
        template = self._create_template("Create Task Template Negative Offset")

        with self.assertRaises(BadRequestException) as context:
            service.create_task_template(
                template.id, SaveTaskTemplateDTO(title="Task", start_date_offset=-1)
            )

        self.assertIn("negative", str(context.exception).lower())

    def test_create_task_template_invalid_duration(self):
        """Test create_task_template rejects a duration of zero or less"""
        service = self._get_service()
        template = self._create_template("Create Task Template Invalid Duration")

        with self.assertRaises(BadRequestException) as context:
            service.create_task_template(template.id, SaveTaskTemplateDTO(title="Task", duration_days=0))

        self.assertIn("at least 1 day", str(context.exception).lower())

        with self.assertRaises(BadRequestException):
            service.create_task_template(template.id, SaveTaskTemplateDTO(title="Task", duration_days=-5))

    def test_create_task_template_no_offset_or_duration(self):
        """Test that start_date_offset and duration_days are optional: omitting them
        skips validation entirely and stores None on the template"""
        service = self._get_service()
        template = self._create_template("Create Task Template No Offset")

        task_template = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="No Offset Task")
        )

        self.assertIsNone(task_template.start_date_offset)
        self.assertIsNone(task_template.duration_days)

    def test_get_task_template(self):
        """Test get_task_template returns the task template, and raises when it does not exist"""
        service = self._get_service()
        template = self._create_template("Get Task Template")
        task_template = service.create_task_template(template.id, SaveTaskTemplateDTO(title="Task"))

        found = service.get_task_template(task_template.id)
        self.assertEqual(found.id, task_template.id)
        self.assertEqual(found.title, "Task")

        with self.assertRaises(NotFoundException):
            service.get_task_template("unknown-task-id")

    def test_get_root_tasks_of_template(self):
        """Test get_root_tasks_of_template returns only root task templates"""
        service = self._get_service()
        template = self._create_template("Get Root Tasks Of Template")

        self.assertEqual(len(service.get_root_tasks_of_template(template.id)), 0)

        root_1 = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Root 1", allow_subtasks=True)
        )
        root_2 = service.create_task_template(template.id, SaveTaskTemplateDTO(title="Root 2"))
        service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Subtask"), parent_task_id=root_1.id
        )

        root_tasks = service.get_root_tasks_of_template(template.id)

        # The subtask is not returned, only the two roots
        self.assertEqual(len(root_tasks), 2)
        self.assertEqual({task.id for task in root_tasks}, {root_1.id, root_2.id})

    def test_get_subtasks_of_task_template(self):
        """Test get_subtasks_of_task_template returns the direct children only"""
        service = self._get_service()
        template = self._create_template("Get Subtasks Of Task Template")

        parent = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Parent", allow_subtasks=True)
        )
        self.assertEqual(len(service.get_subtasks_of_task_template(parent.id)), 0)

        child = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Child", allow_subtasks=True), parent_task_id=parent.id
        )
        # Grandchild must not be returned as a subtask of the parent
        service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Grandchild"), parent_task_id=child.id
        )

        subtasks = service.get_subtasks_of_task_template(parent.id)

        self.assertEqual(len(subtasks), 1)
        self.assertEqual(subtasks[0].id, child.id)

        with self.assertRaises(NotFoundException):
            service.get_subtasks_of_task_template("unknown-task-id")

    def test_update_task_template(self):
        """Test update_task_template updates the editable fields"""
        service = self._get_service()
        template = self._create_template("Update Task Template")

        task_template = service.create_task_template(
            template.id,
            SaveTaskTemplateDTO(
                title="Old Title",
                start_date_offset=0,
                duration_days=5,
                priority=TaskPriority.LOW,
                assign_to_role="developer",
            ),
        )

        updated = service.update_task_template(
            task_template.id,
            UpdateTaskTemplateDTO(
                title="New Title",
                start_date_offset=3,
                duration_days=8,
                priority=TaskPriority.HIGH,
                assign_to_role="project_manager",
            ),
        )

        self.assertEqual(updated.id, task_template.id)
        self.assertEqual(updated.title, "New Title")
        self.assertEqual(updated.start_date_offset, 3)
        self.assertEqual(updated.duration_days, 8)
        self.assertEqual(updated.priority, TaskPriority.HIGH)
        self.assertEqual(updated.assign_to_role, "project_manager")

    def test_update_task_template_not_found(self):
        """Test update_task_template raises when the task template does not exist"""
        service = self._get_service()

        with self.assertRaises(NotFoundException):
            service.update_task_template(
                "unknown-task-id",
                UpdateTaskTemplateDTO(
                    title="Title", start_date_offset=0, duration_days=1, priority=TaskPriority.MEDIUM
                ),
            )

    def test_update_task_template_negative_offset(self):
        """Test update_task_template rejects a negative start date offset"""
        service = self._get_service()
        template = self._create_template("Update Task Template Negative Offset")
        task_template = service.create_task_template(template.id, SaveTaskTemplateDTO(title="Task"))

        with self.assertRaises(BadRequestException) as context:
            service.update_task_template(
                task_template.id,
                UpdateTaskTemplateDTO(
                    title="Task", start_date_offset=-1, duration_days=1, priority=TaskPriority.MEDIUM
                ),
            )

        self.assertIn("negative", str(context.exception).lower())

    def test_update_task_template_invalid_duration(self):
        """Test update_task_template rejects a duration of zero or less"""
        service = self._get_service()
        template = self._create_template("Update Task Template Invalid Duration")
        task_template = service.create_task_template(template.id, SaveTaskTemplateDTO(title="Task"))

        with self.assertRaises(BadRequestException) as context:
            service.update_task_template(
                task_template.id,
                UpdateTaskTemplateDTO(
                    title="Task", start_date_offset=0, duration_days=0, priority=TaskPriority.MEDIUM
                ),
            )

        self.assertIn("at least 1 day", str(context.exception).lower())

    def test_delete_task_template(self):
        """Test delete_task_template removes the task template and all its descendants"""
        service = self._get_service()
        template = self._create_template("Delete Task Template")

        parent = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Parent", allow_subtasks=True)
        )
        child = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Child", allow_subtasks=True), parent_task_id=parent.id
        )
        grandchild = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Grandchild"), parent_task_id=child.id
        )
        # A sibling root that must survive the delete
        other_root = service.create_task_template(template.id, SaveTaskTemplateDTO(title="Other Root"))

        service.delete_task_template(parent.id)

        # The whole subtree is gone (recursive cascade)
        for deleted_id in [parent.id, child.id, grandchild.id]:
            self.assertFalse(TaskTemplate.select().where(TaskTemplate.id == deleted_id).exists())

        # The unrelated root is untouched
        self.assertTrue(TaskTemplate.select().where(TaskTemplate.id == other_root.id).exists())

    def test_delete_task_template_not_found(self):
        """Test delete_task_template raises when the task template does not exist"""
        service = self._get_service()

        with self.assertRaises(NotFoundException):
            service.delete_task_template("unknown-task-id")

    def test_update_task_template_description(self):
        """Test update_task_template_description stores the new rich text"""
        service = self._get_service()
        template = self._create_template("Update Task Template Description")
        task_template = service.create_task_template(template.id, SaveTaskTemplateDTO(title="Task"))

        rich_text = RichText()
        rich_text.add_paragraph("Define the project scope and requirements.")

        updated = service.update_task_template_description(task_template.id, rich_text.to_dto())

        self.assert_json(updated.description.to_json_dict(), rich_text.to_dto().to_json_dict())
        # The description is persisted
        self.assert_json(
            service.get_task_template(task_template.id).description.to_json_dict(),
            rich_text.to_dto().to_json_dict(),
        )

    def test_update_priority(self):
        """Test update_priority sets the new priority"""
        service = self._get_service()
        template = self._create_template("Update Priority")
        task_template = service.create_task_template(
            template.id, SaveTaskTemplateDTO(title="Task", priority=TaskPriority.LOW)
        )

        updated = service.update_priority(task_template.id, TaskPriority.HIGH)

        self.assertEqual(updated.priority, TaskPriority.HIGH)
        self.assertEqual(service.get_task_template(task_template.id).priority, TaskPriority.HIGH)

    def test_update_priority_not_found(self):
        """Test update_priority raises when the task template does not exist"""
        service = self._get_service()

        with self.assertRaises(NotFoundException):
            service.update_priority("unknown-task-id", TaskPriority.HIGH)
