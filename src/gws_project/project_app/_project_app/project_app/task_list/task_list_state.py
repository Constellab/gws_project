from typing import Any, Dict, List, Optional

import reflex as rx
from gws_project.task.task_dto import TaskDTO, TaskStatus
from gws_project.task.task_service import TaskService
from gws_reflex_main import ConfirmDialogState, ReflexMainState
from kanban.kanban import CardMoveEvent

from ..common.breadcrumb.breadcrumb_state import Task
from ..common.project_page_state import ProjectPageState, ProjectUrlParam
from ..task_form.task_form_dialog_state import TaskFormDialogState


class TaskListState(ReflexMainState):
    """State for managing the task list within a project.

    This state handles fetching and displaying tasks for a specific project,
    as well as managing task deletion.
    """

    _url_params: Optional[ProjectUrlParam] = None

    _tasks: List[Task] = []

    @rx.var
    async def get_tasks(self) -> List[TaskDTO]:

        project_state = await self.get_state(ProjectPageState)
        url_param = await project_state.get_url_params()

        previous_id = self._url_params.id if self._url_params else None
        current_id = url_param.id if url_param else None
        if previous_id != current_id:
            self._url_params = url_param
            task_service = TaskService()
            with await self.authenticate_user():
                if url_param and url_param.type == "project":
                    self._tasks = task_service.get_root_tasks_of_project(url_param.id)
                elif url_param and url_param.type == "task":
                    self._tasks = task_service.get_subtasks(url_param.id)
                else:
                    self._tasks = []

        return [task.to_dto() for task in self._tasks]

    def delete_task(self, task_id: str):
        """Delete a task and its subtasks from the state.

        :param task_id: The ID of the task to delete
        :type task_id: str
        """
        if self._tasks:
            self._tasks = [task for task in self._tasks if task.id != task_id]

    def add_or_update_task(self, task: Task):
        """Update a task in the state.

        :param updated_task: The updated TaskDTO
        :type updated_task: TaskDTO
        """
        if not self._tasks:
            return

        for i, task_ in enumerate(self._tasks):
            if task_.id == task.id:
                self._tasks[i] = task
                return

        self._tasks.append(task)

    @rx.var
    async def kanban_board_data(self) -> Dict[str, Any]:
        """Convert tasks to Kanban board format.

        :return: Dictionary with columns structure for the Kanban board
        :rtype: Dict[str, Any]
        """
        # Group tasks by status
        tasks = await self.get_tasks
        todo_tasks = [task for task in tasks if task.status == TaskStatus.TODO]
        doing_tasks = [task for task in tasks if task.status == TaskStatus.DOING]
        done_tasks = [task for task in tasks if task.status == TaskStatus.DONE]

        def task_to_card(task: TaskDTO) -> Dict[str, Any]:
            """Convert a TaskDTO to a Kanban card format."""
            return {
                "id": task.id,
                "title": task.title,
                "description": task.description or "",
                "priority": task.priority.value,
                "assignee": task.assign_to.first_name + ' ' + task.assign_to.last_name if task.assign_to else "Unassigned",
            }

        return {
            "columns": [
                {
                    "id": TaskStatus.TODO.value,
                    "title": "To Do",
                    "cards": [task_to_card(task) for task in todo_tasks]
                },
                {
                    "id": TaskStatus.DOING.value,
                    "title": "In Progress",
                    "cards": [task_to_card(task) for task in doing_tasks]
                },
                {
                    "id": TaskStatus.DONE.value,
                    "title": "Done",
                    "cards": [task_to_card(task) for task in done_tasks]
                }
            ]
        }

    @rx.event(background=True)  # type: ignore
    async def handle_card_move(self, event_dict: dict):
        """Handle card movement in the Kanban board.

        :param new_board: The updated board structure
        :param card: The card that was moved
        :param source: Source column information
        :param destination: Destination column information
        """
        event = CardMoveEvent.from_json(event_dict)
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        try:
            # Extract task ID and new status from destination column
            task_id = event.card_id
            new_status_str = event.to_column_id

            if not task_id or not new_status_str:
                yield rx.toast.error("Invalid card move data")
                return

            # Convert status string to TaskStatus enum
            new_status = TaskStatus[new_status_str]

            # Update task status
            with await main_state.authenticate_user():
                task_service = TaskService()
                task = task_service.update_status(task_id, new_status)

                async with self:
                    await self._update_task(task)

        except Exception as e:
            yield rx.toast.error(f"Error moving task: {str(e)}")

    async def _update_task(self, task: Task):
        """Update a task in the state.

        :param task: The updated TaskDTO
        :type task: TaskDTO
        """
        if not self._tasks:
            return

        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                break

    async def handle_card_click(self, card_id: str, metadata: Dict, lane_id: str):
        """Handle card click in the Kanban board.

        :param card_id: The ID of the clicked card
        :param metadata: Card metadata
        :param lane_id: The column ID
        """
        # Navigate to task detail page
        return rx.redirect(f"/task/{card_id}")

    async def open_update_task_dialog(self, task: TaskDTO):
        """Open the update task dialog.

        :param task: The task to update
        :type task: TaskDTO
        """
        form_state = await self.get_state(TaskFormDialogState)

        await form_state.open_update_dialog(
            task=task,
            callback_after_close=self._on_update_task_dialog_close
        )

    async def _on_update_task_dialog_close(self, task: Task):
        """Callback after the update task dialog is closed to refresh the task list.

        :param task: The updated task
        :type task: Task
        """
        self.add_or_update_task(task)

    @rx.event
    async def open_delete_task_dialog(self, task: TaskDTO):
        """Open the delete task confirmation dialog.

        :param task: The task to delete
        :type task: TaskDTO
        """
        delete_dialog_state = await self.get_state(ConfirmDialogState)

        # Build confirmation message
        warning = ""
        if task.allow_subtasks:
            warning = " This will also delete all its subtasks."

        delete_dialog_state.open_dialog(
            title="Delete Task",
            content=f"Are you sure you want to delete this task?{warning}",
            action=lambda: self._delete_action(task.id)
        )

    async def _delete_action(self, task_id: str):
        """Delete the task from the list."""
        with await self.authenticate_user():
            task_service = TaskService()
            task_service.delete_task(task_id)

        # Show success toast
        yield rx.toast.success("Task deleted successfully")

        # Remove from list
        self.delete_task(task_id)
