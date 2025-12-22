
import reflex as rx
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_dto import TaskTemplateDTO
from gws_project.template.task_template_service import TaskTemplateService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..task_template_form_dialog import TaskTemplateFormDialogState
from ..template_page_state import TemplatePageState, TemplateUrlParam


class TaskTemplateListState(ReflexMainState):
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
    async def get_task_templates(self) -> list[TaskTemplateDTO]:
        """Get all task templates for the current project template.

        :return: List of task template DTOs
        :rtype: List[TaskTemplateDTO]
        """
        template_state = await self.get_state(TemplatePageState)
        url_param = await template_state.get_url_params()

        previous_id = self._url_params.id if self._url_params else None
        current_id = url_param.id if url_param else None
        if previous_id != current_id:
            self._url_params = url_param
            task_template_service = TaskTemplateService()
            with await self.authenticate_user():
                if url_param and url_param.type == "template":
                    self._task_templates = task_template_service.get_root_tasks_of_template(url_param.id)
                elif url_param and url_param.type == "task_template":
                    self._task_templates = task_template_service.get_subtasks_of_task_template(url_param.id)
                else:
                    self._task_templates = []

        return [task_template.to_dto() for task_template in self._task_templates]

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
        with await self.authenticate_user():
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
            with await self.authenticate_user():
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
        with await self.authenticate_user():
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
