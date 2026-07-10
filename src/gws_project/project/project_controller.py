from fastapi.param_functions import Depends
from gws_core import AuthorizationService

from gws_project.core.project_api import project_api
from gws_project.project.project_count_dto import ChildrenCountDTO, ProjectCountDTO
from gws_project.project.project_service import ProjectService
from gws_project.task.task_service import TaskService


@project_api.get(
    "/project/count",
    tags=["Project"],
    summary="Count current user's projects by status",
)
def count_current_user_projects(
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> ProjectCountDTO:
    """Count all projects for the current user, grouped by status
    (total, ongoing, done, todo)."""
    return ProjectService().count_current_user_projects()


@project_api.get(
    "/project/{project_id}/children-count",
    tags=["Project"],
    summary="Get direct children counts for a project",
)
def get_project_children_count(
    project_id: str,
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> ChildrenCountDTO:
    """Get the number of direct root tasks and documents for a project."""
    return ProjectService().get_project_children_count(project_id)


@project_api.get(
    "/task/{task_id}/children-count",
    tags=["Task"],
    summary="Get direct children counts for a task",
)
def get_task_children_count(
    task_id: str,
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> ChildrenCountDTO:
    """Get the number of direct subtasks and documents for a task."""
    return TaskService().get_task_children_count(task_id)
