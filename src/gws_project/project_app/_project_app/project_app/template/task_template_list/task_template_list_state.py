
import reflex as rx
from gws_core import BaseModelDTO
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_dto import TaskTemplateDTO
from gws_project.template.task_template_service import TaskTemplateService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..task_template_form_dialog import TaskTemplateFormDialogState
from ..template_page_state import TemplatePageState, TemplateUrlParam


class TaskTemplateRowDTO(BaseModelDTO):
    """A task template annotated with whether it can be moved up/down among the
    sibling templates that share its start_date_offset (used to enable/disable the
    move up/down menu items in the table).

    A pydantic DTO (not a plain dataclass), so the nested `template` field's own
    fields (title, start_date_offset, ...) bind correctly as Reflex Vars in the
    frontend - a dataclass wrapping a pydantic model does not serialize its nested
    fields the same way.
    """

    template: TaskTemplateDTO
    can_move_up: bool
    can_move_down: bool


class TaskTemplateListState(rx.State):
    """State for managing the task template list within a project template.

    This state handles fetching and displaying task templates for a specific project template,
    as well as managing task template deletion.
    """

    _url_params: TemplateUrlParam | None = None

    _task_templates: list[TaskTemplate] = []

    @rx.var
    async def current_url_id(self) -> str:
        """Get the current URL ID to watch for changes and force component remount.

        This var is used to detect URL changes and ensure proper reloading when
        navigating between task templates.

        :return: Current URL ID
        :rtype: str
        """
        template_state = await self.get_state(TemplatePageState)
        current_object = await template_state.get_object()

        if not current_object:
            return ""

        return current_object.id

    @rx.var
    async def task_template_count(self) -> int:
        """Get the count of task templates in the current list.

        :return: Number of task templates
        :rtype: int
        """
        templates = await self.get_task_templates
        return len(templates)

    @rx.var
    async def get_task_templates(self) -> list[TaskTemplateRowDTO]:
        """Get all task templates for the current project template.

        :return: List of task template rows, annotated with move up/down eligibility
        :rtype: List[TaskTemplateRowDTO]
        """
        template_state = await self.get_state(TemplatePageState)
        url_param = await template_state.get_url_params()

        previous_id = self._url_params.id if self._url_params else None
        current_id = url_param.id if url_param else None
        if previous_id != current_id:
            self._url_params = url_param
            task_template_service = TaskTemplateService()
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                if url_param and url_param.type == "template":
                    self._task_templates = task_template_service.get_root_tasks_of_template(url_param.id)
                elif url_param and url_param.type == "task_template":
                    self._task_templates = task_template_service.get_subtasks_of_task_template(url_param.id)
                else:
                    self._task_templates = []

        return self._build_rows()

    def _build_rows(self) -> list[TaskTemplateRowDTO]:
        """Build the display rows from `_task_templates`.

        `_task_templates` is already ordered by (start_date_offset, order_index), so a
        template can move up if the previous one shares its offset, and down if the
        next one does - no separate query needed to know that.

        :return: List of task template rows
        :rtype: List[TaskTemplateRowDTO]
        """
        rows: list[TaskTemplateRowDTO] = []
        last_index = len(self._task_templates) - 1
        for index, task_template in enumerate(self._task_templates):
            can_move_up = (
                index > 0
                and self._task_templates[index - 1].start_date_offset == task_template.start_date_offset
            )
            can_move_down = (
                index < last_index
                and self._task_templates[index + 1].start_date_offset == task_template.start_date_offset
            )
            rows.append(
                TaskTemplateRowDTO(
                    template=task_template.to_dto(),
                    can_move_up=can_move_up,
                    can_move_down=can_move_down,
                )
            )
        return rows

    @rx.event
    async def move_task_template_up(self, task_template_id: str):
        """Move a task template up among the sibling templates that share its start offset.

        :param task_template_id: The ID of the task template to move
        :type task_template_id: str
        """
        await self._move_task_template(task_template_id, "up")

    @rx.event
    async def move_task_template_down(self, task_template_id: str):
        """Move a task template down among the sibling templates that share its start offset.

        :param task_template_id: The ID of the task template to move
        :type task_template_id: str
        """
        await self._move_task_template(task_template_id, "down")

    async def _move_task_template(self, task_template_id: str, direction: str):
        """Move a task template and refresh the local list to reflect the new order.

        :param task_template_id: The ID of the task template to move
        :type task_template_id: str
        :param direction: "up" or "down"
        :type direction: str
        """
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_template_service = TaskTemplateService()
            task_template_service.move_task_template(task_template_id, direction)

            # Refresh the cached list so the new order is reflected
            if self._url_params and self._url_params.type == "template":
                self._task_templates = task_template_service.get_root_tasks_of_template(
                    self._url_params.id
                )
            elif self._url_params and self._url_params.type == "task_template":
                self._task_templates = task_template_service.get_subtasks_of_task_template(
                    self._url_params.id
                )

    def delete_task_template(self, task_template_id: str):
        """Delete a task template from the state.

        :param task_template_id: The ID of the task template to delete
        :type task_template_id: str
        """
        if self._task_templates:
            self._task_templates = [tt for tt in self._task_templates if tt.id != task_template_id]

    def add_or_update_task_template(self, task_template: TaskTemplate):
        """Add or update a task template in the state.

        :param task_template: The task template to add or update
        :type task_template: TaskTemplate
        """
        if self._task_templates is None:
            return

        for i, tt in enumerate(self._task_templates):
            if tt.id == task_template.id:
                self._task_templates[i] = task_template
                return

        self._task_templates.append(task_template)

    @rx.event
    async def open_delete_task_template_dialog(self, task_template: TaskTemplateDTO):
        """Open the delete task template confirmation dialog.

        :param task_template: The task template to delete
        :type task_template: TaskTemplateDTO
        """
        delete_dialog_state = await self.get_state(ConfirmDialogState)

        # Build confirmation message
        warning = ""
        if task_template.allow_subtasks:
            warning = " This will also delete all its descendants (subtask templates, sub-subtask templates, etc.)."

        delete_dialog_state.open_dialog(
            title="Delete Task Template",
            content=f"Are you sure you want to delete this task template?{warning}",
            action=lambda: self._delete_action(task_template.id)
        )

    async def _delete_action(self, task_template_id: str):
        """Delete the task template from the list."""
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_template_service = TaskTemplateService()
            task_template_service.delete_task_template(task_template_id)

        # Show success toast
        yield rx.toast.success("Task template deleted successfully")

        # Remove from list
        self.delete_task_template(task_template_id)

    @rx.event
    async def open_create_task_template_dialog(self):
        """Open the create task template dialog.

        This method opens the dialog for creating a new root task template.
        """
        template_state = await self.get_state(TemplatePageState)
        url_param = await template_state.get_url_params()

        if not url_param:
            yield rx.toast.error("No template context found")
            return

        # Determine the project template ID based on URL param type
        if url_param.type == "template":
            project_template_id = url_param.id
        elif url_param.type == "task_template":
            # If we're viewing a task template, we need to get its parent template
            task_template_service = TaskTemplateService()
            main_state = await self.get_state(ReflexMainState)
            with await main_state.authenticate_user():
                task_template = task_template_service.get_task_template(url_param.id)
                project_template_id = task_template.project_template.id
        else:
            yield rx.toast.error("Invalid template context")
            return

        # Open the dialog
        dialog_state = await self.get_state(TaskTemplateFormDialogState)
        await dialog_state.open_create_dialog(
            project_template_id=project_template_id,
            callback_after_close=self._on_task_template_created_or_updated
        )

    @rx.event
    async def open_update_task_template_dialog(self, task_template_id: str):
        """Open the update task template dialog.

        :param task_template_id: The ID of the task template to update
        :type task_template_id: str
        """
        # Get the task template
        task_template_service = TaskTemplateService()
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_template = task_template_service.get_task_template(task_template_id)

        # Open the dialog
        dialog_state = await self.get_state(TaskTemplateFormDialogState)
        await dialog_state.open_update_dialog(
            task_template=task_template,
            callback_after_close=self._on_task_template_created_or_updated
        )

    async def _on_task_template_created_or_updated(self, task_template: TaskTemplate):
        """Callback after a task template is created or updated.

        :param task_template: The created or updated task template
        :type task_template: TaskTemplate
        """
        # Add or update in the list
        self.add_or_update_task_template(task_template)
