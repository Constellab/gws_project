from typing import Any, Dict, List

import reflex as rx
from gws_core import Logger
from gws_project.project.project import Project
from gws_project.project_app._project_app.custom_components.kanban.kanban import \
    CardMoveEvent
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskDTO, TaskStatus
from gws_project.task.task_service import TaskService
from gws_reflex_main import ReflexMainState


class TaskListState(ReflexMainState):
    """State for managing the task list within a project.

    This state handles fetching and displaying tasks for a specific project,
    as well as managing task deletion.
    """

    tasks: List[TaskDTO] = []
    is_loading: bool = False
    error_message: str = ""

    async def load_tasks(self, project_id: str):
        """Load all tasks for a specific project.

        :param project_id: The ID of the project
        :type project_id: str
        """

        self.is_loading = True
        self.error_message = ""

        try:
            tasks: List[Task]
            with await self.authenticate_user():
                # Get the project by ID
                project = Project.get_by_id_and_check(project_id)
                # Get all tasks for the project
                tasks = Task.get_tasks_of_project(project)

            # Filter to only root tasks (tasks without parent)
            root_tasks = [task for task in tasks if task.is_root_task()]

            # Convert tasks to DTOs
            self.tasks = [task.to_dto() for task in root_tasks]

        except Exception as e:
            Logger.log_exception_stack_trace(e)
            self.error_message = f"Error loading tasks: {str(e)}"
            self.tasks = []

        finally:
            self.is_loading = False

    @rx.event(background=True)  # type: ignore
    async def delete_task(self, task_id: str):
        """Delete a task and reload the task list.

        :param task_id: The ID of the task to delete
        :type task_id: str
        """
        main_state: ReflexMainState
        async with self:
            main_state = await self.get_state(ReflexMainState)

        try:
            # Delete the task
            with await main_state.authenticate_user():
                task_service = TaskService()
                task_service.delete_task(task_id)

            # Show success toast
            yield rx.toast.success("Task deleted successfully")

            # Reload tasks - we need to get the project_id from the current tasks
            async with self:
                if self.tasks:
                    project_id = self.tasks[0].project_id
                    await self.load_tasks(project_id)

        except Exception as e:
            yield rx.toast.error(f"Error deleting task: {str(e)}")

    @rx.var
    def kanban_board_data(self) -> Dict[str, Any]:
        """Convert tasks to Kanban board format.

        :return: Dictionary with columns structure for the Kanban board
        :rtype: Dict[str, Any]
        """
        # Group tasks by status
        todo_tasks = [task for task in self.tasks if task.status == TaskStatus.TODO]
        doing_tasks = [task for task in self.tasks if task.status == TaskStatus.DOING]
        done_tasks = [task for task in self.tasks if task.status == TaskStatus.DONE]

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
                    await self._update_task(task.to_dto())

        except Exception as e:
            yield rx.toast.error(f"Error moving task: {str(e)}")

    async def _update_task(self, task: TaskDTO):
        """Update a task in the state.

        :param task: The updated TaskDTO
        :type task: TaskDTO
        """
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
