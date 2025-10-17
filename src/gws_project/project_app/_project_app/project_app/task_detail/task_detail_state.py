from typing import List, Optional

import reflex as rx
from gws_core.user.user_dto import UserDTO
from gws_project.project.project import Project
from gws_project.project.project_dto import ProjectDTO
from gws_project.task.task import Task
from gws_project.task.task_dto import TaskDTO
from gws_project.task.task_service import TaskService
from gws_reflex_main import ReflexMainState


class TaskDetailState(ReflexMainState):
    """State for managing the task detail page.

    This state handles fetching and displaying the details of a single task
    based on the task ID from the URL.
    """

    task: Optional[TaskDTO] = None
    project: Optional[ProjectDTO] = None
    parent_task: Optional[TaskDTO] = None
    subtasks: List[TaskDTO] = []
    is_loading: bool = False
    error_message: str = ""

    async def load_task(self, task_id: str):
        """Load the task details based on the task ID.

        :param task_id: The ID of the task to load
        :type task_id: str
        """
        # Check authentication before accessing data
        if not await self.check_authentication():
            self.error_message = "You must be authenticated to view task details"
            return

        self.is_loading = True
        self.error_message = ""

        try:
            task: Optional[Task]
            project: Optional[Project]
            with await self.authenticate_user():
                task_service = TaskService()
                task = task_service.get_task(task_id)
                self.task = task.to_dto()

                # Load the project
                project = task.project
                self.project = project.to_dto()

                # Load parent task if this is a subtask
                if task.parent_task:
                    self.parent_task = task.parent_task.to_dto()
                else:
                    self.parent_task = None

                # Load subtasks if the task allows them
                if task.allow_subtasks:
                    subtasks = task.get_subtasks()
                    self.subtasks = [subtask.to_dto() for subtask in subtasks]
                else:
                    self.subtasks = []

        except Exception as e:
            self.error_message = f"Error loading task: {str(e)}"
            self.task = None
            self.project = None
            self.parent_task = None
            self.subtasks = []

        finally:
            self.is_loading = False

    async def on_load(self):
        """Event handler called when the page loads.

        This method is automatically called by Reflex when the page is loaded.
        It extracts the task_id from the URL and loads the task.
        """
        # Get task_id from the router
        if self.get_task_id():
            await self.load_task(self.get_task_id())
        else:
            self.error_message = "No task ID provided"

    def get_task_id(self) -> str:
        """Return the current task ID from the URL."""
        return self.task_id_param  # from the URL parameter

