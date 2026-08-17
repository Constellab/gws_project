
import reflex as rx
from gws_core import RichTextDTO
from gws_project.template.project_template_dto import ProjectTemplateDTO
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_dto import TaskPriority, TaskTemplateDTO
from gws_project.template.task_template_service import TaskTemplateService
from gws_reflex_main import ConfirmDialogState, I18nState, ReflexMainState, toast_tr

from ...common.project_app_router import ProjectAppRouter
from ...common.timestamp_text_component import format_timestamp
from ..task_template_form_dialog.task_template_form_dialog_state import TaskTemplateFormDialogState
from ..template_page_state import TemplatePageState
from . import task_template_detail_translations  # noqa: F401  (side effect: registers translations)


class TaskTemplateDetailState(rx.State):
    """State for managing the task template detail page.

    This state handles fetching and displaying the details of a single task template
    based on the task template ID from the URL.
    """

    description_edit_mode: bool = False  # Track if description is in edit mode
    view_mode: str = "subtasks"  # View mode for tabs

    @rx.var
    async def task_template(self) -> TaskTemplateDTO | None:
        """Return the current task template DTO.

        :return: The current task template DTO
        :rtype: Optional[TaskTemplateDTO]
        """
        template_page_state = await self.get_state(TemplatePageState)
        current_object = await template_page_state.task_template()
        if current_object:
            return current_object.to_dto()
        return None

    @rx.var
    async def created_at_text(self) -> str:
        """Return the formatted creation timestamp of the current task template.

        :return: The formatted timestamp, or "" if there is no current task template
        :rtype: str
        """
        task_template = await self.task_template
        return format_timestamp(task_template.created_at) if task_template else ""

    @rx.var
    async def last_modified_at_text(self) -> str:
        """Return the formatted last-modified timestamp of the current task template.

        :return: The formatted timestamp, or "" if there is no current task template
        :rtype: str
        """
        task_template = await self.task_template
        return format_timestamp(task_template.last_modified_at) if task_template else ""

    async def _get_project_template(self) -> ProjectTemplateDTO | None:
        """Return the current project template DTO.

        :return: The current project template DTO
        :rtype: Optional[ProjectTemplateDTO]
        """
        template_page_state = await self.get_state(TemplatePageState)
        current_object = await template_page_state.project_template()
        if current_object:
            return current_object.to_dto()
        return None

    @rx.var
    async def parent_task_template(self) -> TaskTemplateDTO | None:
        """Return the parent task template DTO if this is a subtask template.

        :return: The parent task template DTO or None
        :rtype: Optional[TaskTemplateDTO]
        """
        template_page_state = await self.get_state(TemplatePageState)
        current_task_template = await template_page_state.task_template()

        if not current_task_template or not current_task_template.parent_task:
            return None

        return current_task_template.parent_task.to_dto()

    async def open_create_subtask_template_dialog(self):
        """Open the create subtask template dialog."""
        from ..task_template_form_dialog.task_template_form_dialog_state import (
            TaskTemplateFormDialogState,
        )

        form_state = await self.get_state(TaskTemplateFormDialogState)

        task_template = await self.task_template

        project_template = await self._get_project_template()
        await form_state.open_create_sub_dialog(
            parent_task_template_id=task_template.id,
            project_template_id=project_template.id,
            callback_after_close=self._on_create_subtask_template_dialog_close
        )

    async def _on_create_subtask_template_dialog_close(self, task_template: TaskTemplate):
        """Callback after the create subtask template dialog is closed to refresh subtasks."""
        # Refresh the page to show the new subtask template
        from ..task_template_list.task_template_list_state import TaskTemplateListState
        task_template_list_state = await self.get_state(TaskTemplateListState)
        task_template_list_state.add_or_update_task_template(task_template)

    async def open_update_task_template_dialog(self):
        """Open the update task template dialog for this task template."""
        form_state = await self.get_state(TaskTemplateFormDialogState)

        # Get the TaskTemplate object (not DTO) from TemplatePageState
        template_page_state = await self.get_state(TemplatePageState)
        task_template = await template_page_state.task_template()

        if not task_template:
            yield await toast_tr.error(self, "task_template_detail.task_template_not_found")
            return

        await form_state.open_update_dialog(
            task_template=task_template,
            callback_after_close=self._on_update_task_template_dialog_close
        )

    async def _on_update_task_template_dialog_close(self, _: TaskTemplate):
        """Callback after the update task template dialog is closed to refresh the task template.

        :param task_template: The updated task template
        :type task_template: TaskTemplate
        """
        # Refresh the current task template by reloading from the page state
        template_page_state = await self.get_state(TemplatePageState)
        await template_page_state.refresh_object()

    def toggle_description_edit_mode(self):
        """Toggle the description edit mode."""
        self.description_edit_mode = not self.description_edit_mode

    def set_view_mode(self, value: str | list[str]):
        """Set the view mode for the tabs.

        :param value: The view mode value
        :type value: Union[str, List[str]]
        """
        if isinstance(value, list):
            self.view_mode = value[0] if value else "subtasks"
        else:
            self.view_mode = value

    @rx.event
    async def handle_description_change(self, event_data: dict):
        """Handle changes from the rich text component and update the task template description.

        Args:
            event_data: Dictionary containing the RichTextDTO data
        """
        # Convert event data to RichTextDTO
        description_dto = RichTextDTO.from_json(event_data)

        # Get current task template
        task_template = await self.task_template
        if not task_template:
            return

        # Update the task template description
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_template_service = TaskTemplateService()
            task_template_service.update_task_template_description(
                task_template.id,
                description_dto
            )

        # Reload the task template to reflect changes
        template_page_state = await self.get_state(TemplatePageState)
        await template_page_state.refresh_object()

    @rx.event
    async def open_delete_task_template_dialog(self):
        """Open the delete task template confirmation dialog."""
        task_template = await self.task_template
        if not task_template:
            yield
            return

        delete_dialog_state = await self.get_state(ConfirmDialogState)
        i18n = await self.get_state(I18nState)

        # Build confirmation message
        warning = ""
        if task_template.allow_subtasks:
            warning = i18n.tr("task_template_detail.delete_dialog_warning")

        delete_dialog_state.open_dialog(
            title=i18n.tr("task_template_detail.delete_dialog_title"),
            content=f"{i18n.tr('task_template_detail.delete_dialog_content')}{warning}",
            action=self._delete_task_template_action
        )

    async def _delete_task_template_action(self):
        """Action to delete the task template after confirmation."""
        task_template = await self.task_template
        if not task_template:
            yield
            return

        # Delete the task template
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_template_service = TaskTemplateService()
            task_template_service.delete_task_template(task_template.id)

        # Show success toast
        yield await toast_tr.success(self, "task_template_detail.deleted_toast")

        # Navigate based on context
        template_page_state = await self.get_state(TemplatePageState)
        current_object = await template_page_state.get_object()

        if isinstance(current_object, TaskTemplate):
            if current_object.parent_task:
                # If we are on a subtask template's detail page, redirect to parent task template
                yield rx.redirect(ProjectAppRouter.get_task_template_detail_url(current_object.parent_task.id))
            else:
                # If we are on the deleted task template's detail page, redirect to project template detail
                yield rx.redirect(ProjectAppRouter.get_project_template_detail_url(current_object.project_template.id))

    async def update_priority(self, new_priority: str):
        """Handle priority change for the task template.

        :param new_priority: The new priority string
        :type new_priority: str
        """
        task_template = await self.task_template
        if not task_template:
            yield await toast_tr.error(self, "task_template_detail.task_template_not_found")
            return

        # create TaskPriority enum from string
        task_priority = TaskPriority[new_priority]

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_template_service = TaskTemplateService()
            task_template_service.update_priority(task_template.id, task_priority)

        # Refresh the current task template
        template_page_state = await self.get_state(TemplatePageState)
        await template_page_state.refresh_object()
