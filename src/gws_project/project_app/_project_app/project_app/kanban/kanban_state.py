from typing import Dict, List

import reflex as rx
from gws_project.task.task_dto import TaskDTO, TaskStatus
from gws_project.task.task_service import TaskService
from gws_reflex_main import ConfirmDialogState, ReflexMainState

from ..common.breadcrumb.breadcrumb_state import Task
from ..common.kanban.kanban import (BoardDataDTO, CardDTO, CardMoveEvent,
                                    ColumnDTO)
from ..task_form.task_form_dialog_state import TaskFormDialogState


class KanbanState(ReflexMainState):
    """State for managing the kanban board view of all tasks.

    This state handles fetching and displaying all tasks accessible to the user
    in a kanban board format, as well as managing task updates and deletion.
    """

    tasks: List[TaskDTO] = []
    _is_loaded: bool = False

    async def load_tasks(self):
        """Fetch all tasks accessible to the current user.

        Uses the task_service.search method without parameters to get all tasks
        from all projects the user has access to.

        :return: List of all tasks as DTOs
        :rtype: List[TaskDTO]
        """
        task_service = TaskService()

        tasks: List[Task]
        with await self.authenticate_user():
            tasks = task_service.search()

        self.tasks = [task.to_dto() for task in tasks]

    async def on_load(self):
        """Event handler called when the page loads.

        Resets the loaded state to force a fresh fetch of tasks.
        """
        await self.load_tasks()

    def delete_task(self, task_id: str):
        """Delete a task and its subtasks from the state.

        :param task_id: The ID of the task to delete
        :type task_id: str
        """
        if self.tasks:
            self.tasks = [task for task in self.tasks if task.id != task_id]

    def add_or_update_task(self, task: Task):
        """Update a task in the state or add it if it doesn't exist.

        :param task: The updated Task entity
        :type task: Task
        """
        if not self.tasks:
            return

        for i, task_ in enumerate(self.tasks):
            if task_.id == task.id:
                self.tasks[i] = task
                return

        self.tasks.append(task)

    @rx.var
    async def kanban_board_data(self) -> BoardDataDTO:
        """Convert tasks to Kanban board format.

        :return: BoardDataDTO with columns structure for the Kanban board
        :rtype: BoardDataDTO
        """
        # Group tasks by status
        tasks = self.tasks
        todo_tasks = [task for task in tasks if task.status == TaskStatus.TODO]
        doing_tasks = [task for task in tasks if task.status == TaskStatus.DOING]
        done_tasks = [task for task in tasks if task.status == TaskStatus.DONE]

        return BoardDataDTO(
            columns=[
                ColumnDTO(
                    id=TaskStatus.TODO.value,
                    title="To Do",
                    cards=[self._task_to_card(task) for task in todo_tasks]
                ),
                ColumnDTO(
                    id=TaskStatus.DOING.value,
                    title="In Progress",
                    cards=[self._task_to_card(task) for task in doing_tasks]
                ),
                ColumnDTO(
                    id=TaskStatus.DONE.value,
                    title="Done",
                    cards=[self._task_to_card(task) for task in done_tasks]
                )
            ]
        )

    def _task_to_card(self, task: TaskDTO) -> CardDTO:
        """Convert a TaskDTO to a Kanban card format."""
        assignee = task.assign_to.first_name + ' ' + task.assign_to.last_name if task.assign_to else "Unassigned"
        return CardDTO(
            id=task.id,
            title=task.title,
            description=(task.description or '').strip(),
            priority=task.priority.value,
            assignee=assignee,
            parent_task_title=task.parent_task_title,
            is_leaf=not task.allow_subtasks
        )

    @rx.event(background=True)  # type: ignore
    async def handle_card_move(self, event_dict: dict):
        """Handle card movement in the Kanban board.

        :param event_dict: The event data containing card move information
        :type event_dict: dict
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

        :param task: The updated Task entity
        :type task: Task
        """
        if not self.tasks:
            return

        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
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
