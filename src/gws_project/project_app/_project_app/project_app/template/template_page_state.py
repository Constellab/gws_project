from dataclasses import dataclass
from typing import Literal

import reflex as rx
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.project_template_service import ProjectTemplateService
from gws_project.template.task_template import TaskTemplate
from gws_project.template.task_template_service import TaskTemplateService
from gws_reflex_main import ReflexMainState


@dataclass
class TemplateUrlParam:
    id: str
    type: Literal["template", "task_template"]


class TemplatePageState(rx.State):
    """State for managing template and task template objects with caching.

    This state provides a centralized way to load and cache ProjectTemplate and TaskTemplate objects
    across the application, avoiding redundant database queries.
    The get_object method automatically detects object type and ID from URL parameters.
    """

    # Private cache for storing the loaded object
    _cached_object: ProjectTemplate | TaskTemplate | None = None

    async def get_url_params(self) -> TemplateUrlParam | None:
        """Get the current object ID from URL parameters.

        This method checks for task_template_id_param and project_template_id_param in the URL
        and returns the corresponding ID.

        :return: The TemplateUrlParam if found, else None
        :rtype: Optional[TemplateUrlParam]
        """
        task_template_id = getattr(self, 'task_template_id_param', None)
        if task_template_id:
            return TemplateUrlParam(id=task_template_id, type="task_template")

        project_template_id = getattr(self, 'project_template_id_param', None)
        if project_template_id:
            return TemplateUrlParam(id=project_template_id, type="template")

        return None

    async def project_template(self) -> ProjectTemplate | None:
        """Get the current project template from URL parameters.

        :return: The loaded ProjectTemplate object, or None if not found
        :rtype: Optional[ProjectTemplate]
        """
        obj = await self.get_object()
        if isinstance(obj, ProjectTemplate):
            return obj

        if isinstance(obj, TaskTemplate):
            return obj.project_template

        return None

    async def task_template(self) -> TaskTemplate | None:
        """Get the current task template from URL parameters.

        :return: The loaded TaskTemplate object, or None if not found
        :rtype: Optional[TaskTemplate]
        """
        obj = await self.get_object()
        if isinstance(obj, TaskTemplate):
            return obj
        return None

    async def get_object(self) -> ProjectTemplate | TaskTemplate | None:
        """Get the current project template or task template from URL parameters with caching.

        This method automatically detects the object type and ID from URL parameters:
        - If task_template_id_param exists in URL: loads TaskTemplate
        - If project_template_id_param exists in URL: loads ProjectTemplate
        - Otherwise: returns None

        The cache stores the actual object. If the requested ID matches the cached object's ID,
        the cached object is returned directly without reloading from the database.

        :return: The loaded ProjectTemplate or TaskTemplate object, or None if not found
        :rtype: Union[ProjectTemplate, TaskTemplate, None]
        """
        # Detect object type and ID from URL parameters
        task_template_id = getattr(self, 'task_template_id_param', None)
        project_template_id = getattr(self, 'project_template_id_param', None)

        # Determine which object to load
        if task_template_id:
            object_id = task_template_id
        elif project_template_id:
            object_id = project_template_id
        else:
            return None

        # Check if we already have this object cached
        if self._cached_object is not None and self._cached_object.id == object_id:
            # Return cached object
            return self._cached_object

        # Load the object based on URL parameter
        main_state = await self.get_state(ReflexMainState)
        with await main_state.authenticate_user():
            if task_template_id:
                task_template_service = TaskTemplateService()
                obj = task_template_service.get_task_template(task_template_id)
                # Update cache
                self._cached_object = obj
                return obj
            elif project_template_id:
                template_service = ProjectTemplateService()
                obj = template_service.get_template(project_template_id)
                # Update cache
                self._cached_object = obj
                return obj
            else:
                return None

    async def refresh_object(self) -> ProjectTemplate | TaskTemplate | None:
        """Refresh (reload) the current object from URL parameters.

        This method forces a reload of the object from the database, even if it's cached.
        Useful when you know the object has been modified and need fresh data.

        :return: The reloaded ProjectTemplate or TaskTemplate object, or None if not found
        :rtype: Union[ProjectTemplate, TaskTemplate, None]
        """
        # Clear the cache to force a reload
        self._cached_object = None

        # Load the object (which will update the cache)
        return await self.get_object()
