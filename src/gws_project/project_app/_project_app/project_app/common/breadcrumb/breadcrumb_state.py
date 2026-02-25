from dataclasses import dataclass

import reflex as rx
from gws_project.project.project import Project
from gws_project.task.task import Task

from ..project_app_router import ProjectAppRouter
from ..projects.project_page_state import ProjectPageState


@dataclass
class BreadcrumbItem:
    """Represents a single item in the breadcrumb trail.

    :param label: The display text for this breadcrumb item
    :type label: str
    :param url: The URL to navigate to when clicked
    :type url: str
    """

    label: str
    url: str


class BreadcrumbState(rx.State):
    """State for managing the breadcrumb navigation component.

    This state builds breadcrumb trails by getting objects from ProjectPageState.
    """

    @rx.var
    async def breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb items for the current page.

        This method gets the current object from ProjectPageState and builds
        the breadcrumb trail based on the object type.

        :return: List of breadcrumb items
        :rtype: List[BreadcrumbItem]
        """
        # Get the ProjectPageState for cached object loading
        page_state = await self.get_state(ProjectPageState)

        # Get the object (auto-detects from URL)
        obj = await page_state.get_object()

        if obj is None:
            return []

        # Start with base breadcrumb
        items = [BreadcrumbItem(label="Projects", url=ProjectAppRouter.get_project_list_url())]

        # Build breadcrumb based on object type
        if isinstance(obj, Task):
            items.extend(self._build_breadcrumb_for_task(obj))
        elif isinstance(obj, Project):
            items.extend(self._build_breadcrumb_for_project(obj))

        return items

    def _build_breadcrumb_for_project(self, project: Project) -> list[BreadcrumbItem]:
        """Build breadcrumb items for a project.

        :param project: The project object
        :type project: Project
        :return: List of breadcrumb items for the project
        :rtype: List[BreadcrumbItem]
        """
        return [
            BreadcrumbItem(
                label=project.title, url=ProjectAppRouter.get_project_detail_url(project.id)
            )
        ]

    def _build_breadcrumb_for_task(self, task: Task) -> list[BreadcrumbItem]:
        """Build breadcrumb items for a task.

        This includes the project, all ancestor tasks (for unlimited hierarchy), and the task itself.

        :param task: The task object
        :type task: Task
        :return: List of breadcrumb items for the task hierarchy
        :rtype: List[BreadcrumbItem]
        """
        items = []

        # Add project
        project = task.project
        items.append(
            BreadcrumbItem(
                label=project.title, url=ProjectAppRouter.get_project_detail_url(project.id)
            )
        )

        # Add all ancestor tasks in order from root to immediate parent
        # Using get_ancestors() which returns [parent, grandparent, ..., root]
        # We reverse it to get [root, ..., grandparent, parent]
        if task.parent_task:
            ancestors = task.get_ancestors()
            # Reverse to show from root to immediate parent
            for ancestor in reversed(ancestors):
                items.append(
                    BreadcrumbItem(
                        label=ancestor.title,
                        url=ProjectAppRouter.get_task_detail_url(ancestor.id),
                    )
                )

        # Add current task
        items.append(
            BreadcrumbItem(label=task.title, url=ProjectAppRouter.get_task_detail_url(task.id))
        )

        return items
