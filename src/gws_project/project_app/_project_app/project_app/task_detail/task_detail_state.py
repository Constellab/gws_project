import reflex as rx
from gws_core import RichTextDTO, UserDTO
from gws_project.project.project_count_dto import ChildrenCountDTO
from gws_project.project.project_dto import ProjectDTO
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskDTO, TaskPriority, TaskStatus
from gws_project.task.task_service import TaskService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.project_app_router import ProjectAppRouter
from ..common.projects.project_page_state import ProjectPageState
from ..common.view_mode_state import ViewModeState
from ..move_task_dialog.move_task_dialog_state import MoveTaskDialogState
from ..task_form.task_form_dialog_state import TaskFormDialogState
from ..task_list.task_list_state import TaskListState


class TaskDetailState(rx.State):
    """State for managing the task detail page.

    This state handles fetching and displaying the details of a single task
    based on the task ID from the URL.
    """

    description_edit_mode: bool = False  # Track if description is in edit mode

    @rx.var
    async def view_mode(self) -> str:
        """Get the current view mode from ViewModeState.

        If the task does not allow subtasks and the current mode is "list",
        falls back to "description" since the subtasks tab is not available.

        :return: The current view mode
        :rtype: str
        """
        view_mode_state = await self.get_state(ViewModeState)
        mode = view_mode_state.view_mode

        # If the task has no subtasks tab, prevent "list" mode
        task = await self.task
        if task and not task.allow_subtasks and mode == "list":
            return "description"

        return mode

    async def set_view_mode(self, value: str | list[str]):
        """Set the view mode by delegating to ViewModeState.

        :param value: The view mode value
        :type value: Union[str, List[str]]
        """
        view_mode_state = await self.get_state(ViewModeState)
        view_mode_state.set_view_mode(value)

    @rx.var
    async def task(self) -> TaskDTO | None:
        """Return the current task DTO.

        :return: The current task DTO
        :rtype: Optional[TaskDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_object = await project_page_state.task()
        if current_object:
            return current_object.to_dto()
        return None

    async def _get_project(self) -> ProjectDTO | None:
        """Return the current project DTO.

        :return: The current project DTO
        :rtype: Optional[ProjectDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_object = await project_page_state.project()
        if current_object:
            return current_object.to_dto()
        return None

    @rx.var
    async def parent_task(self) -> TaskDTO | None:
        """Return the parent task DTO if this is a subtask.

        :return: The parent task DTO or None
        :rtype: Optional[TaskDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_task = await project_page_state.task()

        if not current_task or not current_task.parent_task:
            return None

        return current_task.parent_task.to_dto()

    @rx.var
    async def subtask_members(self) -> list[UserDTO]:
        """Return the list of unique users assigned to subtasks of this task.

        Only returns data if the task allows subtasks.

        :return: List of unique user DTOs assigned to subtasks
        :rtype: List[UserDTO]
        """
        task = await self.task
        if not task or not task.allow_subtasks:
            return []

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            users = task_service.get_descendants_assigned_users(task.id)
            return [user.to_dto() for user in users]

    @rx.var
    async def children_count(self) -> ChildrenCountDTO | None:
        """Get the number of subtasks and documents for this task.

        :return: ChildrenCountDTO with subtask_count and document_count
        :rtype: Optional[ChildrenCountDTO]
        """
        task = await self.task
        if not task:
            return None

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            return task_service.get_task_children_count(task.id)

    async def open_create_subtask_dialog(self):
        """Open the create subtask dialog."""

        form_state = await self.get_state(TaskFormDialogState)

        task = await self.task

        await form_state.open_create_sub_dialog(
            parent_task_id=task.id,
            project=await self._get_project(),
            callback_after_close=self._on_create_subtask_dialog_close,
        )

    async def _on_create_subtask_dialog_close(self, task: Task):
        """Callback after the create subtask dialog is closed to refresh subtasks."""
        # Currently, no specific action is needed here.
        task_list_state = await self.get_state(TaskListState)

        await task_list_state.add_or_update_task(task)

    async def open_update_task_dialog(self):
        """Open the update task dialog for this task."""
        form_state = await self.get_state(TaskFormDialogState)

        # Get the Task object (not DTO) from ProjectPageState
        project_page_state = await self.get_state(ProjectPageState)
        task = await project_page_state.task()

        if not task:
            yield rx.toast.error("Task not found")
            return

        await form_state.open_update_dialog(
            task=task, callback_after_close=self._on_update_task_dialog_close
        )

    async def _on_update_task_dialog_close(self, _: Task):
        """Callback after the update task dialog is closed to refresh the task.

        :param task: The updated task
        :type task: Task
        """
        # Refresh the current task by reloading from the page state
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()

    @rx.event
    async def open_move_task_dialog(self):
        """Open the move task dialog for the currently viewed task."""
        task = await self.task
        if not task:
            yield rx.toast.error("Task not found")
            return

        move_dialog_state = await self.get_state(MoveTaskDialogState)
        await move_dialog_state.open_move_dialog(
            task=task, callback_after_close=self._on_task_moved
        )

    async def _on_task_moved(self, _: Task):
        """Callback after the currently viewed task is moved.

        The task keeps the same ID (and URL) and its own subtasks are unaffected by the
        move, so we only need to refresh its cached project/parent task relationship,
        used by the breadcrumb and the details sidebar.

        :param task: The moved task
        :type task: Task
        """
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()

    def toggle_description_edit_mode(self):
        """Toggle the description edit mode."""
        self.description_edit_mode = not self.description_edit_mode

    @rx.event
    async def handle_description_change(self, event_data: dict):
        """Handle changes from the rich text component and update the task description.

        Args:
            event_data: Dictionary containing the RichTextDTO data
        """
        # Convert event data to RichTextDTO
        description_dto = RichTextDTO.from_json(event_data)

        # Get current task
        task = await self.task
        if not task:
            return

        # Update the task description
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            task_service.update_task_description(task.id, description_dto)

        # Reload the task to reflect changes
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()

    @rx.event
    async def open_delete_task_dialog(self):
        """Open the delete task confirmation dialog."""
        task = await self.task
        if not task:
            yield
            return

        delete_dialog_state = await self.get_state(ConfirmDialogState)

        # Build confirmation message
        warning = " Its documents and notes will be permanently deleted."

        if task.allow_subtasks:
            warning = (
                " This will also permanently delete all its descendants "
                "(subtasks, sub-subtasks, etc.) and their documents and notes."
            )

        delete_dialog_state.open_dialog(
            title="Delete Task",
            content=f"Are you sure you want to delete this task?{warning}",
            action=self._delete_task_action,
        )

    async def _delete_task_action(self):
        """Action to delete the task after confirmation."""
        task = await self.task
        if not task:
            yield
            return

        # Delete the task
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            task_service.delete_task(task.id)

        # Show success toast
        yield rx.toast.success("Task deleted successfully")

        # Navigate based on context
        project_page_state = await self.get_state(ProjectPageState)
        current_object = await project_page_state.get_object()

        if isinstance(current_object, Task):
            if current_object.parent_task:
                # If we are on a subtask's detail page, redirect to parent task
                yield rx.redirect(
                    ProjectAppRouter.get_task_detail_url(current_object.parent_task.id)
                )
            else:
                # If we are on the deleted task's detail page, redirect to project detail
                yield rx.redirect(
                    ProjectAppRouter.get_project_detail_url(current_object.project.id)
                )

    @rx.event
    async def open_change_task_type_dialog(self):
        """Open a confirmation dialog to change the task type (allow_subtasks)."""
        task = await self.task
        if not task:
            yield
            return

        confirm_dialog_state = await self.get_state(ConfirmDialogState)

        if task.allow_subtasks:
            # Converting parent -> leaf
            confirm_dialog_state.open_dialog(
                title="Convert to normal task",
                content="Are you sure you want to convert this task to a normal task? "
                "Status, priority, dates and progress will become manually managed.",
                action=self._change_task_type_action,
            )
        else:
            # Converting leaf -> parent
            confirm_dialog_state.open_dialog(
                title="Convert to task with subtasks",
                content="Are you sure you want to convert this task to a task with subtasks? "
                "Status, priority, dates and progress will be automatically calculated from subtasks.",
                action=self._change_task_type_action,
            )

    async def _change_task_type_action(self):
        """Action to toggle the task type after confirmation."""
        task = await self.task
        if not task:
            yield
            return

        new_allow_subtasks = not task.allow_subtasks

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            task_service.update_allow_subtasks(task.id, new_allow_subtasks)

        yield rx.toast.success("Task type changed successfully")

        # Refresh the current task
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()

        # Refresh the task list
        task_list_state = await self.get_state(TaskListState)
        task_list_state.clear_state()  # Clear task list state to force reload of tasks when navigating back to list

    async def update_status(self, new_status: str):
        """Handle status change for the task.

        :param new_status: The new status string
        :type new_status: str
        """
        task = await self.task
        if not task:
            yield rx.toast.error("Task not found")
            return

        # create TaskStatus enum from string
        task_status = TaskStatus[new_status]

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            task_service.update_status(task.id, task_status)

        # Refresh the current task
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()

    async def update_priority(self, new_priority: str):
        """Handle priority change for the task.

        :param new_priority: The new priority string
        :type new_priority: str
        """
        task = await self.task
        if not task:
            yield rx.toast.error("Task not found")
            return

        # create TaskPriority enum from string
        task_priority = TaskPriority[new_priority]

        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            task_service = TaskService()
            task_service.update_priority(task.id, task_priority)

        # Refresh the current task
        project_page_state = await self.get_state(ProjectPageState)
        await project_page_state.refresh_object()
