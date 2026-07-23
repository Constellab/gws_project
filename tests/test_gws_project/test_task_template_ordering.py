from gws_core import BadRequestException, BaseTestCase
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.project_template_dto import SaveProjectTemplateDTO
from gws_project.template.project_template_service import ProjectTemplateService
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_dto import SaveTaskTemplateDTO
from gws_project.template.task_template_service import TaskTemplateService
from gws_project.user.project_user_sync_service import ProjectUserSyncService


# test_task_template_ordering
class TestTaskTemplateOrdering(BaseTestCase):
    """Test suite for task template ordering (by start_date_offset, with order_index as a
    tiebreaker for tied offsets) and for TaskTemplateService.move_task_template, which lets
    the user reorder templates within a tied-offset group."""

    @classmethod
    def init_before_test(cls):
        super().init_before_test()
        ProjectUserSyncService().sync_all_users()

    def _get_project_template_service(self) -> ProjectTemplateService:
        return ProjectTemplateService()

    def _get_task_template_service(self) -> TaskTemplateService:
        return TaskTemplateService()

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
    # Ordering by start_date_offset
    # ------------------------------------------------------------------

    def test_root_templates_ordered_by_start_offset_ascending(self):
        """Root task templates are sorted by start_date_offset, not creation order"""
        template = self._create_project_template("Offset Order Root")
        later = self._create_task_template(template, "Later", start_date_offset=10)
        earlier = self._create_task_template(template, "Earlier", start_date_offset=2)
        middle = self._create_task_template(template, "Middle", start_date_offset=5)

        ordered = TaskTemplate.get_root_tasks_of_template(template.id)

        self.assertEqual([t.id for t in ordered], [earlier.id, middle.id, later.id])

    def test_subtask_templates_ordered_by_start_offset_ascending(self):
        """Subtask templates are sorted by start_date_offset, not creation order"""
        template = self._create_project_template("Offset Order Sub")
        parent = self._create_task_template(template, "Parent", allow_subtasks=True)
        later = self._create_task_template(
            template, "Later", parent_task_id=parent.id, start_date_offset=10
        )
        earlier = self._create_task_template(
            template, "Earlier", parent_task_id=parent.id, start_date_offset=2
        )

        ordered = TaskTemplate.get_subtasks_of_template_task(parent.id)

        self.assertEqual([t.id for t in ordered], [earlier.id, later.id])

    def test_tied_offset_templates_keep_creation_order(self):
        """Templates sharing the same start_date_offset keep their creation order"""
        template = self._create_project_template("Offset Tie")
        first = self._create_task_template(template, "First", start_date_offset=3)
        second = self._create_task_template(template, "Second", start_date_offset=3)
        third = self._create_task_template(template, "Third", start_date_offset=3)

        ordered = TaskTemplate.get_root_tasks_of_template(template.id)

        self.assertEqual([t.id for t in ordered], [first.id, second.id, third.id])

    # ------------------------------------------------------------------
    # move_task_template
    # ------------------------------------------------------------------

    def test_move_root_template_up_and_down_within_tied_group(self):
        """Moving a template up/down swaps it with its neighbor within the tied-offset group"""
        task_template_service = self._get_task_template_service()
        template = self._create_project_template("Move Root Tied")
        first = self._create_task_template(template, "First", start_date_offset=3)
        second = self._create_task_template(template, "Second", start_date_offset=3)
        third = self._create_task_template(template, "Third", start_date_offset=3)

        task_template_service.move_task_template(third.id, "up")
        ordered = TaskTemplate.get_root_tasks_of_template(template.id)
        self.assertEqual([t.id for t in ordered], [first.id, third.id, second.id])

        task_template_service.move_task_template(third.id, "up")
        ordered = TaskTemplate.get_root_tasks_of_template(template.id)
        self.assertEqual([t.id for t in ordered], [third.id, first.id, second.id])

        task_template_service.move_task_template(third.id, "down")
        ordered = TaskTemplate.get_root_tasks_of_template(template.id)
        self.assertEqual([t.id for t in ordered], [first.id, third.id, second.id])

    def test_move_subtask_template_within_tied_group(self):
        """Moving a subtask template only reorders it among its own parent's tied siblings"""
        task_template_service = self._get_task_template_service()
        template = self._create_project_template("Move Sub Tied")
        parent = self._create_task_template(template, "Parent", allow_subtasks=True)
        first = self._create_task_template(
            template, "First", parent_task_id=parent.id, start_date_offset=1
        )
        second = self._create_task_template(
            template, "Second", parent_task_id=parent.id, start_date_offset=1
        )

        task_template_service.move_task_template(second.id, "up")

        ordered = TaskTemplate.get_subtasks_of_template_task(parent.id)
        self.assertEqual([t.id for t in ordered], [second.id, first.id])

    def test_move_does_not_cross_offset_boundary(self):
        """Moving up/down never swaps a template with a neighbor of a different offset"""
        task_template_service = self._get_task_template_service()
        template = self._create_project_template("Move No Cross Boundary")
        before = self._create_task_template(template, "Before", start_date_offset=1)
        first_tied = self._create_task_template(template, "FirstTied", start_date_offset=3)
        second_tied = self._create_task_template(template, "SecondTied", start_date_offset=3)
        after = self._create_task_template(template, "After", start_date_offset=5)

        # first_tied is first within its own tied group (offset=3), even though "before"
        # (offset=1) comes right before it in the full list - moving up must be refused,
        # not silently swap across the offset boundary.
        with self.assertRaises(BadRequestException) as context:
            task_template_service.move_task_template(first_tied.id, "up")
        self.assertIn("already first", str(context.exception).lower())

        # second_tied is last within its tied group, even though "after" (offset=5) comes
        # right after it - moving down must be refused too.
        with self.assertRaises(BadRequestException) as context:
            task_template_service.move_task_template(second_tied.id, "down")
        self.assertIn("already last", str(context.exception).lower())

        # Sanity check: nothing moved
        ordered = TaskTemplate.get_root_tasks_of_template(template.id)
        self.assertEqual(
            [t.id for t in ordered], [before.id, first_tied.id, second_tied.id, after.id]
        )

    def test_move_single_template_in_group_fails_both_directions(self):
        """A template with no tied sibling can't move up or down"""
        task_template_service = self._get_task_template_service()
        template = self._create_project_template("Move Single")
        only = self._create_task_template(template, "Only", start_date_offset=7)

        with self.assertRaises(BadRequestException):
            task_template_service.move_task_template(only.id, "up")
        with self.assertRaises(BadRequestException):
            task_template_service.move_task_template(only.id, "down")

    def test_move_invalid_direction_fails(self):
        """An invalid direction value is rejected"""
        task_template_service = self._get_task_template_service()
        template = self._create_project_template("Move Invalid Direction")
        first = self._create_task_template(template, "First", start_date_offset=1)
        self._create_task_template(template, "Second", start_date_offset=1)

        with self.assertRaises(BadRequestException) as context:
            task_template_service.move_task_template(first.id, "sideways")
        self.assertIn("up", str(context.exception).lower())
