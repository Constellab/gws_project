from datetime import datetime
from enum import Enum
from typing import Literal

import reflex as rx
from gws_core import UserDTO
from gws_project.project.project_dto import ProjectDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_dto import (
    CreateTaskDTO,
    TaskDTO,
    TaskPriority,
    TaskStatus,
    UpdateTaskDTO,
)
from gws_project.task.task_service import TaskService
from gws_reflex_main import FormDialogState, ReflexDialogCloseEvent, ReflexMainState


class TaskFormMode(Enum):
    """Enum representing the different modes of the task form dialog."""
    CREATE_ROOT = "create_root"
    CREATE_SUB = "create_sub"
    UPDATE = "update"


class TaskFormDialogState(FormDialogState, rx.State):
    """State management for the create/update task dialog functionality."""

    _project: ProjectDTO | None = None

    # Task being edited (None for create mode)
    _editing_task: TaskDTO | None = None

    # Project for creating new tasks
    _project: ProjectDTO | None = None

    # Parent task ID for creating subtasks
    _parent_task_id: str = ""

    # Form mode
    _form_mode: str = TaskFormMode.CREATE_ROOT.value

    # List of users available for assignment
    users: list[UserDTO] = []

    # Form field default values
    form_title: str = ""
    form_start_date: str = ""
    form_end_date: str = ""
    form_status: str = TaskStatus.TODO.value
    form_priority: str = TaskPriority.MEDIUM.value
    form_allow_subtasks: bool = False
    form_assign_to_id: str = ""

    # Track selected task type in create root mode
    selected_task_type: Literal['with_children', 'without_children'] = "without_children"

    _callback_after_close: ReflexDialogCloseEvent[Task] | None = None

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
        return self._form_mode == TaskFormMode.CREATE_SUB.value

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

    async def _init_form_fields(self, task: TaskDTO | None = None):
        """Initialize form fields for create or update mode.

        Args:
            task: Optional task to populate form fields from (for update mode)
        """
        if task:
            # Update mode - populate from task
            self.form_title = task.title
            self.form_start_date = task.start_date.strftime('%Y-%m-%d')
            self.form_end_date = task.end_date.strftime('%Y-%m-%d')
            self.form_status = task.status.value if hasattr(task.status, 'value') else task.status
            self.form_priority = task.priority.value if hasattr(task.priority, 'value') else task.priority
            self.form_allow_subtasks = task.allow_subtasks
            self.form_assign_to_id = task.assign_to.id if task.assign_to else ""
            self.selected_task_type = "with_children" if task.allow_subtasks else "without_children"
        else:
            # Create mode - clear/default values
            self.form_title = ""
            self.form_start_date = ""
            self.form_end_date = ""
            self.form_status = TaskStatus.TODO.value
            self.form_priority = TaskPriority.MEDIUM.value
            self.form_allow_subtasks = False
            self.form_assign_to_id = ""
            self.selected_task_type = "without_children"

            # init assign_to_id to current user
            main_state = await self.get_state(ReflexMainState)
            self.form_assign_to_id = (await main_state.get_and_check_current_user()).id

    def _validate_and_extract_common_fields(self, form_data: dict) -> dict:
        """Validate and extract common fields from form data.

        Args:
            form_data: Dictionary containing form fields
            require_dates: Whether dates are required (False for subtasks)
            require_priority: Whether priority is required (False for subtasks)

        Returns:
            Dictionary with validated and parsed common fields

        Raises:
            Exception: If validation fails
        """
        # Get values from form data
        title = form_data.get('title', '').strip()
        assign_to_id = form_data.get('assign_to_id', '').strip() or None

        # Validate required fields
        if not title:
            raise Exception("Task title is required")

        result = {
            'title': title,
            'assign_to_id': assign_to_id
        }

        # if there is no child, the dates, priority and status are required
        if self.selected_task_type == "without_children":

            # Only process dates if required
            start_date_str = form_data.get('start_date', '').strip()
            end_date_str = form_data.get('end_date', '').strip()

            if not start_date_str:
                raise Exception("Start date is required")

            if not end_date_str:
                raise Exception("End date is required")

            # Parse dates from string to date
            result['start_date'] = datetime.fromisoformat(start_date_str).date()
            result['end_date'] = datetime.fromisoformat(end_date_str).date()

            priority_str = form_data.get('priority', TaskPriority.MEDIUM.value)
            result['priority'] = TaskPriority(priority_str)

            status_str = form_data.get('status', TaskStatus.TODO.value)
            result['status'] = TaskStatus(status_str)

        return result

    async def open_create_dialog(self, project: ProjectDTO, callback_after_close: ReflexDialogCloseEvent[Task] = None):
        """Open the dialog in create mode for a new root task.

        This method is kept for backward compatibility and delegates to open_create_root_dialog.

        Args:
            project: The project to create the task for
            callback_after_close: Optional callback to invoke after the dialog closes with the created task
        """
        # Store context
        self._project = project
        self._parent_task_id = ""
        self._form_mode = TaskFormMode.CREATE_ROOT.value
        self._callback_after_close = callback_after_close
        self.is_update_mode = False

        # Initialize form fields
        await self._init_form_fields()

        # Load users for the project
        await self._load_users(project.id)

        # Open the dialog
        await self.open_dialog()

    async def open_create_sub_dialog(self, parent_task_id: str, project: ProjectDTO,
                                     callback_after_close: ReflexDialogCloseEvent[Task] = None):
        """Open the dialog in create mode for a new subtask.

        Args:
            parent_task_id: The ID of the parent task to create the subtask under
            project: The project to create the task for
            callback_after_close: Optional callback to invoke after the dialog closes with the created task
        """
        # Store context
        self._parent_task_id = parent_task_id
        self._project = project
        self._form_mode = TaskFormMode.CREATE_SUB.value
        self._callback_after_close = callback_after_close
        self.is_update_mode = False

        # Initialize form fields
        await self._init_form_fields()

        # Load users for the project
        await self._load_users(project.id)

        # Open the dialog
        await self.open_dialog()

    async def open_update_dialog(self, task: Task, callback_after_close: ReflexDialogCloseEvent[Task] = None):
        """Open the dialog in update mode with existing task data.

        Args:
            task: The task model to update
            callback_after_close: Optional callback to invoke after the dialog closes with the updated task
        """
        # Convert Task to TaskDTO for form display
        task_dto = task.to_dto()

        # Store context
        self._editing_task = task_dto
        self._project = task.project.to_dto()  # Store project from task relationship
        self._parent_task_id = ""
        self._form_mode = TaskFormMode.UPDATE.value
        self._callback_after_close = callback_after_close
        self.is_update_mode = True

        # Initialize form fields with task data
        await self._init_form_fields(task_dto)

        # Load users for the project
        await self._load_users(task.project.id)

        # Open the dialog
        await self.open_dialog()

    def _validate_and_parse_create_task_form_data(self, form_data: dict) -> CreateTaskDTO | None:
        """Validate and parse form data into a CreateTaskDTO for create operations.

        Args:
            form_data: Dictionary containing form fields

        Returns:
            CreateTaskDTO if validation succeeds, None otherwise (error toast is shown)
        """
        # Validate and extract common fields
        common_fields = self._validate_and_extract_common_fields(form_data)
        # Handle radio button value: "with_children" or "without_children"
        allow_subtasks_value = form_data.get('allow_subtasks', 'without_children')
        allow_subtasks = allow_subtasks_value == 'with_children'

        # Create and return CreateTaskDTO for root task
        return CreateTaskDTO(
            title=common_fields['title'],
            start_date=common_fields.get('start_date'),
            end_date=common_fields.get('end_date'),
            status=common_fields.get('status'),
            priority=common_fields.get('priority'),
            allow_subtasks=allow_subtasks,
            assign_to_id=common_fields.get('assign_to_id')
        )

    def _validate_and_parse_update_task_form_data(self, form_data: dict) -> UpdateTaskDTO | None:
        """Validate and parse form data into an UpdateTaskDTO for update operations.

        Args:
            form_data: Dictionary containing form fields

        Returns:
            UpdateTaskDTO if validation succeeds, None otherwise (error toast is shown)
        """
        # Validate and extract common fields
        common_fields = self._validate_and_extract_common_fields(form_data)

        # Create and return UpdateTaskDTO
        return UpdateTaskDTO(
            title=common_fields['title'],
            start_date=common_fields.get('start_date'),
            end_date=common_fields.get('end_date'),
            priority=common_fields.get('priority'),
            status=common_fields.get('status'),
            assign_to_id=common_fields.get('assign_to_id')
        )

    async def _create(self, form_data: dict):
        """Create a new task (root or subtask) using the form data.

        Args:
            form_data: Dictionary containing form fields

        Yields:
            Reflex events (rx.toast)
        """

        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        # Validate and parse form data for create operations
        task_dto = self._validate_and_parse_create_task_form_data(form_data)
        if task_dto is None:
            return  # Validation error already shown

        task: Task = None
        # Create the task based on the form mode
        if self._form_mode == TaskFormMode.CREATE_ROOT.value:
            # Create the root task
            with await main_state.authenticate_user():
                task_service = TaskService()
                task = task_service.create_root_task(self._project.id, task_dto)

            # Show success toast
            yield rx.toast.success("Task created successfully")

        elif self._form_mode == TaskFormMode.CREATE_SUB.value:
            # Create the subtask
            with await main_state.authenticate_user():
                task_service = TaskService()
                task = task_service.create_sub_task(self._parent_task_id, task_dto)

            # Show success toast
            yield rx.toast.success("Subtask created successfully")

        if self._callback_after_close:
            await self._callback_after_close(task)

    async def _update(self, form_data: dict):
        """Update an existing task using the form data.

        Args:
            form_data: Dictionary containing form fields

        Yields:
            Reflex events (rx.toast)
        """

        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        # Validate and parse form data for update operations
        task_dto = self._validate_and_parse_update_task_form_data(form_data)
        if task_dto is None:
            return  # Validation error already shown

        # Update the task
        task: Task
        with await main_state.authenticate_user():
            task_service = TaskService()
            task = task_service.update_task(self._editing_task.id, task_dto)

        # Show success toast
        yield rx.toast.success("Task updated successfully")

        # Invoke callback if provided
        if self._callback_after_close:
            await self._callback_after_close(task)

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self._editing_task = None
        self._project = None
        self._parent_task_id = ""
        self._form_mode = TaskFormMode.CREATE_ROOT.value
        self.users = []
        self.form_title = ""
        self.form_start_date = ""
        self.form_end_date = ""
        self.form_status = TaskStatus.TODO.value
        self.form_priority = TaskPriority.MEDIUM.value
        self.form_allow_subtasks = False
        self.form_assign_to_id = ""
        self.selected_task_type = "without_children"
        self.is_update_mode = False
        self._callback_after_close = None

    async def _load_users(self, project_id: str):
        """Load users available for assignment from the project.

        Args:
            project_id: The ID of the project to load users from
        """
        main_state: ReflexMainState = await self.get_state(ReflexMainState)

        with await main_state.authenticate_user():
            project_service = ProjectService()
            project_users = project_service.get_project_users(project_id)
            # Extract user objects from ProjectUserDTO
            self.users = [project_user.user.to_dto() for project_user in project_users]

    @rx.var
    async def get_min_start_date(self) -> str:
        """Get the minimum start date allowed for the task based on the project start date.

        Returns:
            Minimum start date in 'YYYY-MM-DD' format
        """
        if self._project:
            return self._project.start_date.strftime('%Y-%m-%d')
        return ""

    @rx.var
    async def get_max_end_date(self) -> str:
        """Get the maximum end date allowed for the task based on the project end date.

        Returns:
            Maximum end date in 'YYYY-MM-DD' format
        """
        if self._project:
            return self._project.end_date.strftime('%Y-%m-%d')
        return ""
