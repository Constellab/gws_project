from enum import Enum
from typing import Optional

import reflex as rx
from gws_project.task.task_dto import TaskPriority
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_dto import (SaveTaskTemplateDTO,
                                                    TaskTemplateDTO,
                                                    UpdateTaskTemplateDTO)
from gws_project.template.task_template_service import TaskTemplateService
from gws_reflex_main import (FormDialogState, ReflexDialogCloseEvent,
                             ReflexMainState)


class TaskTemplateFormMode(Enum):
    """Enum representing the different modes of the task template form dialog."""
    CREATE_ROOT = "create_root"
    CREATE_SUB = "create_sub"
    UPDATE = "update"


class TaskTemplateFormDialogState(FormDialogState, rx.State):
    """State management for the create/update task template dialog functionality."""

    # Task template being edited (None for create mode)
    _editing_task_template: Optional[TaskTemplateDTO] = None

    # Project template for creating new task templates
    _project_template_id: str = ""

    # Parent task template ID for creating subtasks
    _parent_task_template_id: str = ""

    # Form mode
    _form_mode: str = TaskTemplateFormMode.CREATE_ROOT.value

    # Form field default values
    form_title: str = ""
    form_description: str = ""
    form_start_date_offset: int = 0
    form_duration_days: int = 1
    form_priority: str = TaskPriority.MEDIUM.value
    form_assign_to_role: str = ""

    # Track selected task type in create root mode
    selected_task_type: str = "without_children"

    _callback_after_close: Optional[ReflexDialogCloseEvent[TaskTemplate]] = None

    def set_selected_task_type(self, value: str):
        """Set the selected task type (with_children or without_children).

        Args:
            value: The selected task type value
        """
        self.selected_task_type = value

    @rx.var
    def is_create_sub_mode(self) -> bool:
        """Check if the form is in CREATE_SUB mode.

        Returns:
            True if in CREATE_SUB mode, False otherwise
        """
        return self._form_mode == TaskTemplateFormMode.CREATE_SUB.value

    @rx.var
    def is_parent_task_in_update_mode(self) -> bool:
        """Check if we're updating a parent task template (task with subtasks).

        Returns:
            True if updating a parent task template, False otherwise
        """
        return self.is_update_mode and self._editing_task_template is not None and self._editing_task_template.allow_subtasks

    @rx.var
    def should_show_dates_and_priority(self) -> bool:
        """Check if dates and priority fields should be shown.

        They should be hidden for:
        - Creating subtasks (dates/priority auto-calculated from parent)
        - Updating parent tasks (dates/priority auto-calculated from children)
        - Creating root tasks with allow_subtasks=True (dates/priority auto-calculated from subtasks)

        Returns:
            True if dates and priority should be shown, False otherwise
        """
        # Hide in create root mode if "Task with subtasks" is selected
        if self.selected_task_type == "with_children":
            return False

        # Show for all other cases (create root without subtasks, update regular task, update subtask)
        return True

    def _init_form_fields(self, task_template: Optional[TaskTemplateDTO] = None):
        """Initialize form fields for create or update mode.

        Args:
            task_template: Optional task template to populate form fields from (for update mode)
        """
        if task_template:
            # Update mode - populate from task template
            self.form_title = task_template.title
            self.form_description = task_template.description or ""
            self.form_start_date_offset = task_template.start_date_offset
            self.form_duration_days = task_template.duration_days
            self.form_priority = task_template.priority.value if hasattr(
                task_template.priority, 'value') else task_template.priority
            self.form_assign_to_role = task_template.assign_to_role or ""
            self.selected_task_type = "with_children" if task_template.allow_subtasks else "without_children"
        else:
            # Create mode - clear/default values
            self.form_title = ""
            self.form_description = ""
            self.form_start_date_offset = 0
            self.form_duration_days = 1
            self.form_priority = TaskPriority.MEDIUM.value
            self.form_assign_to_role = ""
            self.selected_task_type = "without_children"

    def _validate_and_extract_common_fields(self, form_data: dict) -> dict:
        """Validate and extract common fields from form data.

        Args:
            form_data: Dictionary containing form fields

        Returns:
            Dictionary with validated and parsed common fields

        Raises:
            Exception: If validation fails
        """
        # Get values from form data
        title = form_data.get('title', '').strip()
        assign_to_role = form_data.get('assign_to_role', '').strip() or None

        # Validate required fields
        if not title:
            raise Exception("Task template title is required")

        result = {
            'title': title,
            'assign_to_role': assign_to_role
        }

        # If there are no children, the dates and priority are required
        if self.selected_task_type == "without_children":
            # Get and validate start_date_offset
            start_date_offset_str = form_data.get('start_date_offset', '0').strip()
            try:
                start_date_offset = int(start_date_offset_str)
                if start_date_offset < 0:
                    raise Exception("Start date offset cannot be negative")
                result['start_date_offset'] = start_date_offset
            except ValueError:
                raise Exception("Start date offset must be a valid number")

            # Get and validate duration_days
            duration_days_str = form_data.get('duration_days', '1').strip()
            try:
                duration_days = int(duration_days_str)
                if duration_days <= 0:
                    raise Exception("Duration must be at least 1 day")
                result['duration_days'] = duration_days
            except ValueError:
                raise Exception("Duration must be a valid number")

            priority_str = form_data.get('priority', TaskPriority.MEDIUM.value)
            result['priority'] = TaskPriority(priority_str)

        return result

    async def open_create_dialog(self, project_template_id: str,
                                 callback_after_close: ReflexDialogCloseEvent[TaskTemplate] = None):
        """Open the dialog in create mode for a new root task template.

        Args:
            project_template_id: The project template ID to create the task template for
            callback_after_close: Optional callback to invoke after the dialog closes with the created task template
        """
        # Store context
        self._project_template_id = project_template_id
        self._parent_task_template_id = ""
        self._form_mode = TaskTemplateFormMode.CREATE_ROOT.value
        self._callback_after_close = callback_after_close
        self.is_update_mode = False

        # Initialize form fields
        self._init_form_fields()

        # Open the dialog
        await self.open_dialog()

    async def open_create_sub_dialog(self, parent_task_template_id: str, project_template_id: str,
                                     callback_after_close: ReflexDialogCloseEvent[TaskTemplate] = None):
        """Open the dialog in create mode for a new subtask template.

        Args:
            parent_task_template_id: The ID of the parent task template to create the subtask under
            project_template_id: The project template ID
            callback_after_close: Optional callback to invoke after the dialog closes with the created task template
        """
        # Store context
        self._parent_task_template_id = parent_task_template_id
        self._project_template_id = project_template_id
        self._form_mode = TaskTemplateFormMode.CREATE_SUB.value
        self._callback_after_close = callback_after_close
        self.is_update_mode = False

        # Initialize form fields
        self._init_form_fields()

        # Open the dialog
        await self.open_dialog()

    async def open_update_dialog(self, task_template: TaskTemplate,
                                 callback_after_close: ReflexDialogCloseEvent[TaskTemplate] = None):
        """Open the dialog in update mode with existing task template data.

        Args:
            task_template: The task template model to update
            callback_after_close: Optional callback to invoke after the dialog closes with the updated task template
        """
        # Convert TaskTemplate to TaskTemplateDTO for form display
        task_template_dto = task_template.to_dto()

        # Store context
        self._editing_task_template = task_template_dto
        self._project_template_id = task_template.project_template.id
        self._parent_task_template_id = ""
        self._form_mode = TaskTemplateFormMode.UPDATE.value
        self._callback_after_close = callback_after_close
        self.is_update_mode = True

        # Initialize form fields with task template data
        self._init_form_fields(task_template_dto)

        # Open the dialog
        await self.open_dialog()

    def _validate_and_parse_create_task_template_form_data(self, form_data: dict) -> Optional[SaveTaskTemplateDTO]:
        """Validate and parse form data into a CreateTaskTemplateDTO for create operations.

        Args:
            form_data: Dictionary containing form fields

        Returns:
            CreateTaskTemplateDTO if validation succeeds, None otherwise (error toast is shown)
        """
        # Validate and extract common fields
        common_fields = self._validate_and_extract_common_fields(form_data)

        # Handle radio button value: "with_children" or "without_children"
        allow_subtasks_value = form_data.get('allow_subtasks', 'without_children')
        allow_subtasks = allow_subtasks_value == 'with_children'

        # Create and return CreateTaskTemplateDTO
        return SaveTaskTemplateDTO(
            title=common_fields['title'],
            start_date_offset=common_fields.get('start_date_offset', 0),
            duration_days=common_fields.get('duration_days', 1),
            priority=common_fields.get('priority', TaskPriority.MEDIUM),
            allow_subtasks=allow_subtasks,
            assign_to_role=common_fields.get('assign_to_role')
        )

    def _validate_and_parse_update_task_template_form_data(self, form_data: dict) -> Optional[UpdateTaskTemplateDTO]:
        """Validate and parse form data into an UpdateTaskTemplateDTO for update operations.

        Args:
            form_data: Dictionary containing form fields

        Returns:
            UpdateTaskTemplateDTO if validation succeeds, None otherwise (error toast is shown)
        """
        # Validate and extract common fields
        common_fields = self._validate_and_extract_common_fields(form_data)

        # Create and return UpdateTaskTemplateDTO
        return UpdateTaskTemplateDTO(
            title=common_fields['title'],
            start_date_offset=common_fields.get('start_date_offset', 0),
            duration_days=common_fields.get('duration_days', 1),
            priority=common_fields.get('priority', TaskPriority.MEDIUM),
            assign_to_role=common_fields.get('assign_to_role')
        )

    async def _create(self, form_data: dict):
        """Create a new task template (root or subtask) using the form data.

        Args:
            form_data: Dictionary containing form fields

        Yields:
            Reflex events (rx.toast)
        """

        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        # Validate and parse form data for create operations
        task_template_dto = self._validate_and_parse_create_task_template_form_data(form_data)
        if task_template_dto is None:
            return  # Validation error already shown

        task_template: TaskTemplate = None
        # Create the task template based on the form mode
        if self._form_mode == TaskTemplateFormMode.CREATE_ROOT.value:
            # Create the root task template
            with await main_state.authenticate_user():
                task_template_service = TaskTemplateService()
                task_template = task_template_service.create_task_template(
                    self._project_template_id, task_template_dto)

            # Show success toast
            yield rx.toast.success("Task template created successfully")

        elif self._form_mode == TaskTemplateFormMode.CREATE_SUB.value:
            # Create the subtask template
            with await main_state.authenticate_user():
                task_template_service = TaskTemplateService()
                task_template = task_template_service.create_task_template(
                    self._project_template_id, task_template_dto, self._parent_task_template_id)

            # Show success toast
            yield rx.toast.success("Subtask template created successfully")

        if self._callback_after_close:
            await self._callback_after_close(task_template)

    async def _update(self, form_data: dict):
        """Update an existing task template using the form data.

        Args:
            form_data: Dictionary containing form fields

        Yields:
            Reflex events (rx.toast)
        """

        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        # Validate and parse form data for update operations
        task_template_dto = self._validate_and_parse_update_task_template_form_data(form_data)
        if task_template_dto is None:
            return  # Validation error already shown

        # Update the task template
        task_template: TaskTemplate
        with await main_state.authenticate_user():
            task_template_service = TaskTemplateService()
            task_template = task_template_service.update_task_template(
                self._editing_task_template.id, task_template_dto)

        # Show success toast
        yield rx.toast.success("Task template updated successfully")

        # Invoke callback if provided
        if self._callback_after_close:
            await self._callback_after_close(task_template)

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self._editing_task_template = None
        self._project_template_id = ""
        self._parent_task_template_id = ""
        self._form_mode = TaskTemplateFormMode.CREATE_ROOT.value
        self.form_title = ""
        self.form_description = ""
        self.form_start_date_offset = 0
        self.form_duration_days = 1
        self.form_priority = TaskPriority.MEDIUM.value
        self.form_assign_to_role = ""
        self.selected_task_type = "without_children"
        self.is_update_mode = False
        self._callback_after_close = None
