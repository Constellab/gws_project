from dataclasses import dataclass
from enum import Enum
from typing import Literal

import reflex as rx
from gws_core import NotFoundException, UnauthorizedException
from gws_project.project.project import Project
from gws_project.project.project_service import ProjectService
from gws_project.task.task import Task
from gws_project.task.task_service import TaskService
from gws_reflex_main import ReflexMainState


@dataclass
class ProjectUrlParam:
    id: str
    type: Literal["project", "task"]


class ProjectAccessError(Enum):
    """Why the object of the current URL could not be loaded."""

    # The project/task does not exist (deleted, or a wrong id in the URL).
    NOT_FOUND = "not_found"
    # It exists, but the current user is not a member of its project.
    NO_ACCESS = "no_access"


class ProjectPageState(rx.State):
    """State for managing project and task objects with caching.

    This state provides a centralized way to load and cache Project and Task objects
    across the application, avoiding redundant database queries.
    The get_object method automatically detects object type and ID from URL parameters.
    """

    # Private cache for storing the loaded object
    _cached_object: Project | Task | None = None

    # Why the current URL's object could not be loaded, as a ProjectAccessError
    # value ("" when everything is fine). An id in the URL is user input - a stale
    # link, or a project the user was never added to - so a missing or forbidden
    # object is a normal state of the page, not a crash: the detail pages read this
    # to render project_access_error_component instead of their content.
    access_error: str = ""

    async def get_url_params(self) -> ProjectUrlParam | None:
        """Get the current object ID from URL parameters.

        This method checks for task_id_param and project_id_param in the URL
        and returns the corresponding ID.

        :return: The object ID if found, else None
        :rtype: Optional[str]
        """
        task_id = getattr(self, 'task_id_param', None)
        if task_id:
            return ProjectUrlParam(id=task_id, type="task")

        project_id = getattr(self, 'project_id_param', None)
        if project_id:
            return ProjectUrlParam(id=project_id, type="project")

        return None

    async def project(self) -> Project | None:
        """Get the current project from URL parameters.
        The method should not be named get_project because the get_object method
        call a get_project which make the reflex compiler confused.

        :return: The loaded Project object, or None if not found
        :rtype: Optional[Project]
        """
        obj = await self.get_object()
        if isinstance(obj, Project):
            return obj

        if isinstance(obj, Task):
            return obj.project
        return None

    async def task(self) -> Task | None:
        """Get the current task from URL parameters.

        :return: The loaded Task object, or None if not found
        :rtype: Optional[Task]
        """
        obj = await self.get_object()
        if isinstance(obj, Task):
            return obj
        return None

    async def get_object(self) -> Project | Task | None:
        """Get the current project or task from URL parameters with caching.

        This method automatically detects the object type and ID from URL parameters:
        - If task_id_param exists in URL: loads Task
        - If project_id_param exists in URL: loads Project
        - Otherwise: returns None

        The cache stores the actual object. If the requested ID matches the cached object's ID,
        the cached object is returned directly without reloading from the database.

        :return: The loaded Project or Task object, or None if not found
        :rtype: Union[Project, Task, None]
        """
        # Detect object type and ID from URL parameters
        task_id = getattr(self, 'task_id_param', None)
        project_id = getattr(self, 'project_id_param', None)

        # Determine which object to load
        if task_id:
            object_id = task_id
        elif project_id:
            object_id = project_id
        else:
            return None

        # Check if we already have this object cached
        # ID is unique across types, so we only need to check the ID
        if self._cached_object is not None and self._cached_object.id == object_id:
            # Return cached object
            return self._cached_object

        # Load the object based on URL parameter
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            try:
                if task_id:
                    obj = TaskService().get_task(task_id)
                else:
                    obj = ProjectService().get_project(project_id)
            except NotFoundException:
                self._set_access_error(ProjectAccessError.NOT_FOUND)
                return None
            except UnauthorizedException:
                self._set_access_error(ProjectAccessError.NO_ACCESS)
                return None

            # Update cache
            self.access_error = ""
            self._cached_object = obj
            return obj

    def _set_access_error(self, error: ProjectAccessError) -> None:
        """Record why the current URL's object could not be loaded.

        :param error: The reason the object is not available
        :type error: ProjectAccessError
        """
        self.access_error = error.value
        self._cached_object = None

    async def refresh_object(self) -> Project | Task | None:
        """Refresh (reload) the current object from URL parameters.

        This method forces a reload of the object from the database, even if it's cached.
        Useful when you know the object has been modified and need fresh data.

        :return: The reloaded Project or Task object, or None if not found
        :rtype: Union[Project, Task, None]
        """
        # Clear the cache to force a reload
        self._cached_object = None
        self.access_error = ""

        # Load the object (which will update the cache)
        return await self.get_object()
