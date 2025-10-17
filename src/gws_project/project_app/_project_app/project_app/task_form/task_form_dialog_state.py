from datetime import datetime
from enum import Enum
from typing import List, Optional

import reflex as rx
from gws_core import UserDTO
from gws_project.project.project_dto import ProjectDTO, ProjectUserDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_dto import (CreateRootTaskDTO, CreateSubTaskDTO,
                                       TaskDTO, TaskPriority, TaskStatus,
                                       UpdateTaskDTO)
from gws_project.task.task_service import TaskService
from gws_reflex_main import FormDialogState, ReflexMainState


class TaskFormMode(Enum):
    """Enum representing the different modes of the task form dialog."""
    CREATE_ROOT = "create_root"
    CREATE_SUB = "create_sub"
    UPDATE = "update"


class TaskFormDialogState(FormDialogState, rx.State):
    """State management for the create/update task dialog functionality."""

    # Task being edited (None for create mode)
    _editing_task: Optional[TaskDTO] = None

    # Project for creating new tasks
    _project: ProjectDTO | None = None

    # Parent task ID for creating subtasks
    _parent_task_id: str = ""

    # Form mode
    _form_mode: str = TaskFormMode.CREATE_ROOT.value

    # List of users available for assignment
    users: List[UserDTO] = []

    # Form field default values
    form_title: str = ""
    form_description: str = ""
    form_start_date: str = ""
    form_end_date: str = ""
    form_status: str = TaskStatus.TODO.value
    form_priority: str = TaskPriority.MEDIUM.value
    form_allow_subtasks: bool = False
    form_assign_to_id: str = ""

    @rx.var
    def is_create_sub_mode(self) -> bool:
        """Check if the form is in CREATE_SUB mode.

        Returns:
            True if in CREATE_SUB mode, False otherwise
        """
        return self._form_mode == TaskFormMode.CREATE_SUB.value

    @rx.event
    async def open_create_dialog(self, project: ProjectDTO):
        """Open the dialog in create mode for a new root task.

        This method is kept for backward compatibility and delegates to open_create_root_dialog.

        Args:
            project: The project to create the task for
        """
        await self.open_create_root_dialog(project)

    @rx.event
    async def open_create_root_dialog(self, project: ProjectDTO):
        """Open the dialog in create mode for a new root task.

        Args:
            project: The project to create the task for
        """
        # Store the project ID
        self._project = project
        self._parent_task_id = ""

        # Set form mode
        self._form_mode = TaskFormMode.CREATE_ROOT.value

        # Clear form fields
        self.form_title = ""
        self.form_description = ""
        self.form_start_date = ""
        self.form_end_date = ""
        self.form_status = TaskStatus.TODO.value
        self.form_priority = TaskPriority.MEDIUM.value
        self.form_allow_subtasks = False
        self.form_assign_to_id = ""

        # Mark as creating
        self.is_update_mode = False

        # Load users for the project
        await self._load_users(project.id)

        # Open the dialog
        await self.open_dialog()

    @rx.event
    async def open_create_sub_dialog(self, parent_task_id: str, project: ProjectDTO):
        """Open the dialog in create mode for a new subtask.

        Args:
            parent_task_id: The ID of the parent task to create the subtask under
            project: The project to create the task for
        """
        # Store the parent task ID and project ID
        self._parent_task_id = parent_task_id
        self._project = project

        # Set form mode
        self._form_mode = TaskFormMode.CREATE_SUB.value

        # Clear form fields
        self.form_title = ""
        self.form_description = ""
        self.form_start_date = ""
        self.form_end_date = ""
        self.form_status = TaskStatus.TODO.value
        self.form_priority = TaskPriority.MEDIUM.value
        self.form_allow_subtasks = False  # Will not be shown in the form
        self.form_assign_to_id = ""

        # Mark as creating
        self.is_update_mode = False

        # Load users for the project
        await self._load_users(project.id)

        # Open the dialog
        await self.open_dialog()

    @rx.event
    async def open_update_dialog(self, task: TaskDTO):
        """Open the dialog in update mode with existing task data.

        Args:
            task: The task to update
        """
        # Store the task being edited
        self._editing_task = task
        self._parent_task_id = ""

        # Set form mode
        self._form_mode = TaskFormMode.UPDATE.value

        # Initialize form fields with task data
        self.form_title = task.title
        self.form_description = task.description or ""
        # Set date to format 'YYYY-MM-DD' for date input
        self.form_start_date = task.start_date.strftime('%Y-%m-%d')
        self.form_end_date = task.end_date.strftime('%Y-%m-%d')
        self.form_status = task.status.value if hasattr(task.status, 'value') else task.status
        self.form_priority = task.priority.value if hasattr(task.priority, 'value') else task.priority
        self.form_allow_subtasks = task.allow_subtasks
        self.form_assign_to_id = task.assign_to.id if task.assign_to else ""

        # Mark as editing
        self.is_update_mode = True

        # Load users for the project
        await self._load_users(task.project_id)

        # Open the dialog
        await self.open_dialog()

    def _validate_and_parse_create_root_task_form_data(self, form_data: dict) -> Optional[CreateRootTaskDTO]:
        """Validate and parse form data into a CreateRootTaskDTO.

        Args:
            form_data: Dictionary containing form fields

        Returns:
            CreateRootTaskDTO if validation succeeds, None otherwise (error toast is shown)
        """
        # Get values from form data
        title = form_data.get('title', '').strip()
        description = form_data.get('description', '').strip()
        start_date_str = form_data.get('start_date', '').strip()
        end_date_str = form_data.get('end_date', '').strip()
        status_str = form_data.get('status', TaskStatus.TODO.value)
        priority_str = form_data.get('priority', TaskPriority.MEDIUM.value)
        allow_subtasks = form_data.get('allow_subtasks', 'false') == 'true'
        assign_to_id = form_data.get('assign_to_id', '').strip() or None

        # Validate required fields
        if not title:
            raise Exception("Task title is required")

        if not description:
            raise Exception("Task description is required")

        if not start_date_str:
            raise Exception("Start date is required")

        if not end_date_str:
            raise Exception("End date is required")

        # Parse dates from string to date
        start_date = datetime.fromisoformat(start_date_str).date()
        end_date = datetime.fromisoformat(end_date_str).date()

        # Parse status and priority
        status = TaskStatus(status_str)
        priority = TaskPriority(priority_str)

        # Create and return the CreateRootTaskDTO
        return CreateRootTaskDTO(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            priority=priority,
            allow_subtasks=allow_subtasks,
            assign_to_id=assign_to_id
        )

    def _validate_and_parse_create_sub_task_form_data(self, form_data: dict) -> Optional[CreateSubTaskDTO]:
        """Validate and parse form data into a CreateSubTaskDTO.

        Args:
            form_data: Dictionary containing form fields

        Returns:
            CreateSubTaskDTO if validation succeeds, None otherwise (error toast is shown)
        """
        # Get values from form data
        title = form_data.get('title', '').strip()
        description = form_data.get('description', '').strip()
        start_date_str = form_data.get('start_date', '').strip()
        end_date_str = form_data.get('end_date', '').strip()
        status_str = form_data.get('status', TaskStatus.TODO.value)
        priority_str = form_data.get('priority', TaskPriority.MEDIUM.value)
        assign_to_id = form_data.get('assign_to_id', '').strip() or None

        # Validate required fields
        if not title:
            raise Exception("Task title is required")

        if not description:
            raise Exception("Task description is required")

        if not start_date_str:
            raise Exception("Start date is required")

        if not end_date_str:
            raise Exception("End date is required")

        # Parse dates from string to date
        start_date = datetime.fromisoformat(start_date_str).date()
        end_date = datetime.fromisoformat(end_date_str).date()

        # Parse status and priority
        status = TaskStatus(status_str)
        priority = TaskPriority(priority_str)

        # Create and return the CreateSubTaskDTO
        return CreateSubTaskDTO(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            priority=priority,
            assign_to_id=assign_to_id
        )

    def _validate_and_parse_update_form_data(self, form_data: dict) -> Optional[UpdateTaskDTO]:
        """Validate and parse form data into an UpdateTaskDTO.

        Args:
            form_data: Dictionary containing form fields

        Returns:
            UpdateTaskDTO if validation succeeds, None otherwise (error toast is shown)
        """
        # Get values from form data
        title = form_data.get('title', '').strip()
        description = form_data.get('description', '').strip()
        start_date_str = form_data.get('start_date', '').strip()
        end_date_str = form_data.get('end_date', '').strip()
        priority_str = form_data.get('priority', TaskPriority.MEDIUM.value)

        # Validate required fields
        if not title:
            raise Exception("Task title is required")

        if not description:
            raise Exception("Task description is required")

        if not start_date_str:
            raise Exception("Start date is required")

        if not end_date_str:
            raise Exception("End date is required")

        # Parse dates from string to date
        start_date = datetime.fromisoformat(start_date_str).date()
        end_date = datetime.fromisoformat(end_date_str).date()

        # Parse priority
        priority = TaskPriority(priority_str)

        # Create and return the UpdateTaskDTO
        return UpdateTaskDTO(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            priority=priority
        )

    async def _create(self, form_data: dict):
        """Create a new task (root or subtask) using the form data.

        Args:
            form_data: Dictionary containing form fields

        Yields:
            Reflex events (rx.toast)
        """
        from ..task_list.task_list_state import TaskListState
        from ..task_detail.task_detail_state import TaskDetailState

        main_state: ReflexMainState
        task_list_state: TaskListState
        task_detail_state: TaskDetailState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            task_list_state = await self.get_state(TaskListState)
            task_detail_state = await self.get_state(TaskDetailState)

        # Create the task based on the form mode
        if self._form_mode == TaskFormMode.CREATE_ROOT.value:
            # Validate and parse form data for root task
            task_dto = self._validate_and_parse_create_root_task_form_data(form_data)
            if task_dto is None:
                return  # Validation error already shown

            # Create the root task
            with await main_state.authenticate_user():
                task_service = TaskService()
                task_service.create_root_task(self._project.id, task_dto)

            # Show success toast
            yield rx.toast.success("Root task created successfully")

        elif self._form_mode == TaskFormMode.CREATE_SUB.value:
            # Validate and parse form data for subtask
            task_dto = self._validate_and_parse_create_sub_task_form_data(form_data)
            if task_dto is None:
                return  # Validation error already shown

            # Create the subtask
            with await main_state.authenticate_user():
                task_service = TaskService()
                task_service.create_sub_task(self._parent_task_id, task_dto)

            # Show success toast
            yield rx.toast.success("Subtask created successfully")

        # Reload tasks and task detail if applicable
        async with self:
            await task_list_state.load_tasks(self._project.id)
            # Reload task detail if we're on the task detail page (for subtasks)
            if self._form_mode == TaskFormMode.CREATE_SUB.value and task_detail_state.task:
                await task_detail_state.load_task(self._parent_task_id)

    async def _update(self, form_data: dict):
        """Update an existing task using the form data.

        Args:
            form_data: Dictionary containing form fields

        Yields:
            Reflex events (rx.toast)
        """
        from ..task_list.task_list_state import TaskListState
        from ..task_detail.task_detail_state import TaskDetailState

        main_state: ReflexMainState
        task_list_state: TaskListState
        task_detail_state: TaskDetailState
        async with self:
            main_state = await self.get_state(ReflexMainState)
            task_list_state = await self.get_state(TaskListState)
            task_detail_state = await self.get_state(TaskDetailState)

        # Validate and parse form data
        task_dto = self._validate_and_parse_update_form_data(form_data)
        if task_dto is None:
            return  # Validation error already shown

        # Update the task
        with await main_state.authenticate_user():
            task_service = TaskService()
            task_service.update_task(self._editing_task.id, task_dto)

        # Reload tasks and task detail if applicable
        async with self:
            await task_list_state.load_tasks(self._editing_task.project_id)
            # Reload task detail if we're on the task detail page
            if task_detail_state.task and task_detail_state.task.id == self._editing_task.id:
                await task_detail_state.load_task(self._editing_task.id)
            # Reload parent task if we updated a subtask
            elif task_detail_state.task and self._editing_task.parent_task_id:
                await task_detail_state.load_task(self._editing_task.parent_task_id)

        # Show success toast
        yield rx.toast.success("Task updated successfully")

    async def _clear_form_state(self):
        """Clear all form state after successful operation."""
        self._editing_task = None
        self._project = None
        self._parent_task_id = ""
        self._form_mode = TaskFormMode.CREATE_ROOT.value
        self.users = []
        self.form_title = ""
        self.form_description = ""
        self.form_start_date = ""
        self.form_end_date = ""
        self.form_status = TaskStatus.TODO.value
        self.form_priority = TaskPriority.MEDIUM.value
        self.form_allow_subtasks = False
        self.form_assign_to_id = ""
        self.is_update_mode = False

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
