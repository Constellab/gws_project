from typing import List

import reflex as rx
from gws_project.project.project import Project
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskDTO
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
        # Check authentication before accessing data
        if not await self.check_authentication():
            self.error_message = "You must be authenticated to view tasks"
            return

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
            self.error_message = f"Error loading tasks: {str(e)}"
            self.tasks = []

        finally:
            self.is_loading = False

    @rx.event(background=True)
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
