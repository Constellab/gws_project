from typing import List

import reflex as rx
from gws_project.template.project_template import ProjectTemplate
from gws_project.template.task_template import TaskTemplate
from gws_reflex_main import ReflexMainState

from ..common.breadcrumb.breadcrumb_state import BreadcrumbItem
from .template_page_state import TemplatePageState


class TemplateBreadcrumbState(ReflexMainState):
    """State for managing the breadcrumb navigation component in template pages.

    This state builds breadcrumb trails by getting template objects from TemplatePageState.
    """

    @rx.var
    async def breadcrumbs(self) -> List[BreadcrumbItem]:
        """Get breadcrumb items for the current template page.

        This method gets the current template object from TemplatePageState and builds
        the breadcrumb trail based on the object type.

        :return: List of breadcrumb items
        :rtype: List[BreadcrumbItem]
        """
        # Get the TemplatePageState for cached object loading
        page_state = await self.get_state(TemplatePageState)

        # Get the object (auto-detects from URL)
        obj = await page_state.get_object()

        if obj is None:
            return []

        # Start with base breadcrumb
        items = [BreadcrumbItem(label="Templates", url="/templates")]

        # Build breadcrumb based on object type
        if isinstance(obj, TaskTemplate):
            items.extend(self._build_breadcrumb_for_task_template(obj))
        elif isinstance(obj, ProjectTemplate):
            items.extend(self._build_breadcrumb_for_project_template(obj))

        return items

    def _build_breadcrumb_for_project_template(self, project_template: ProjectTemplate) -> List[BreadcrumbItem]:
        """Build breadcrumb items for a project template.

        :param project_template: The project template object
        :type project_template: ProjectTemplate
        :return: List of breadcrumb items for the project template
        :rtype: List[BreadcrumbItem]
        """
        return [
            BreadcrumbItem(label=project_template.name, url=f"/template/project/{project_template.id}")
        ]

    def _build_breadcrumb_for_task_template(self, task_template: TaskTemplate) -> List[BreadcrumbItem]:
        """Build breadcrumb items for a task template.

        This includes the project template, parent task template (if subtask), and the task template itself.

        :param task_template: The task template object
        :type task_template: TaskTemplate
        :return: List of breadcrumb items for the task template hierarchy
        :rtype: List[BreadcrumbItem]
        """
        items = []

        # Add project template
        project_template = task_template.project_template
        items.append(
            BreadcrumbItem(label=project_template.name, url=f"/template/project/{project_template.id}")
        )

        # Add parent task template if this is a subtask template
        if task_template.parent_task:
            parent_task = task_template.parent_task
            items.append(
                BreadcrumbItem(
                    label=parent_task.title,
                    url=f"/template/task/{parent_task.id}"
                )
            )

        # Add current task template
        items.append(
            BreadcrumbItem(label=task_template.title, url=f"/template/task/{task_template.id}")
        )

        return items
