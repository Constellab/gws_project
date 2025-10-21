from typing import List, Optional

import reflex as rx
from gws_project.project.project_dto import ProjectDTO
from gws_project.task.task_dto import TaskDTO
from gws_reflex_main import ReflexMainState

from ..common.project_page_state import ProjectPageState


class TaskDetailState(ReflexMainState):
    """State for managing the task detail page.

    This state handles fetching and displaying the details of a single task
    based on the task ID from the URL.
    """

    _task_id: Optional[str] = None
    _parent_task: Optional[TaskDTO] = None
    _subtasks: List[TaskDTO] = []

    @rx.var
    async def task(self) -> Optional[TaskDTO]:
        """Return the current task DTO.

        :return: The current task DTO
        :rtype: Optional[TaskDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_object = await project_page_state.task()
        if current_object:
            return current_object.to_dto()
        return None

    @rx.var
    async def project(self) -> Optional[ProjectDTO]:
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
    async def parent_task(self) -> Optional[TaskDTO]:
        """Return the parent task DTO if this is a subtask.

        :return: The parent task DTO or None
        :rtype: Optional[TaskDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_task = await project_page_state.task()

        if not current_task:
            self._task_id = None
            self._parent_task = None
            return None

        if self._task_id != current_task.id:
            # Load parent task if this is a subtask
            if current_task.parent_task:
                self._parent_task = current_task.parent_task.to_dto()
            else:
                self._parent_task = None
            self._task_id = current_task.id

        return self._parent_task

    @rx.var
    async def subtasks(self) -> List[TaskDTO]:
        """Return the list of subtasks for the current task.

        :return: List of TaskDTOs
        :rtype: List[TaskDTO]
        """
        project_page_state = await self.get_state(ProjectPageState)
        current_task = await project_page_state.task()

        if not current_task:
            self._task_id = None
            self._subtasks = []
            return []

        if self._task_id != current_task.id:
            # Load subtasks if the task allows them
            if current_task.allow_subtasks:
                subtasks = current_task.get_subtasks()
                self._subtasks = [subtask.to_dto() for subtask in subtasks]
            else:
                self._subtasks = []
            self._task_id = current_task.id

        return self._subtasks

    async def reload_subtasks(self):
        """Reload the subtasks for the current task.

        This method forces a reload of subtasks from the database.
        """
        self._task_id = None
        await self.subtasks

