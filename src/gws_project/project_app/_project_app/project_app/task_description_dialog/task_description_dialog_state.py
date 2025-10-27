from typing import Optional

import reflex as rx
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_project.project_app._project_app.project_app.common.project_page_state import \
    ProjectPageState
from gws_project.task.task_dto import TaskDTO
from gws_project.task.task_service import TaskService
from gws_reflex_main import FormDialogState, ReflexMainState


class TaskDescriptionDialogState(FormDialogState, rx.State):
    """State management for the task description dialog functionality."""

    # Task being edited
    _task_id: Optional[str] = None

    # Form field default values
    form_description_rich_text: Optional[RichTextDTO] = None

    @rx.event
    def handle_description_change(self, event_data: dict):
        """Handle changes from the rich text component.

        Args:
            event_data: Dictionary containing the RichTextDTO data
        """
        # Store the rich text as DTO
        self.form_description_rich_text = RichTextDTO.from_json(event_data)

    @rx.event
    async def open_dialog_with_task(self, task: TaskDTO):
        """Open the dialog with existing task description.

        Args:
            task: The task to edit description for
        """
        # Store the task ID
        self._task_id = task.id

        # Initialize form fields with task data
        self.form_description_rich_text = task.description

        # Mark as update mode (always updating description)
        self.is_update_mode = True

        # Open the dialog
        await self.open_dialog()

    async def _create(self, form_data: dict):
        """Not used for description updates."""
        pass

    async def _update(self, form_data: dict):
        """Update the task description.

        Args:
            form_data: Dictionary containing form fields (not used, we use state variables)

        Yields:
            Reflex events (rx.toast)
        """
        main_state: ReflexMainState
        project_page_state: ProjectPageState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            project_page_state = await self.get_state(ProjectPageState)

        # Update the task description
        with await main_state.authenticate_user():
            task_service = TaskService()
            task_service.update_task_description(
                self._task_id,
                self.form_description_rich_text
            )

        # Reload the task detail state
        async with self:
            await project_page_state.refresh_object()

        # Show success toast
        yield rx.toast.success("Task description updated successfully")

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self._task_id = None
        self.form_description_rich_text = None
        self.is_update_mode = False
