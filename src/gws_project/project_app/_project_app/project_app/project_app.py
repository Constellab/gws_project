import reflex as rx
from gws_reflex_main import register_gws_reflex_app

from .kanban.kanban_component import kanban_page
from .kanban.kanban_state import KanbanState
from .project_detail.project_detail_component import project_detail_page
from .project_list.project_list_component import project_list_page
from .project_list.project_list_state import ProjectListState
from .task_detail.task_detail_component import task_detail_page

app = register_gws_reflex_app()


# Declare the project list page as the index page
@rx.page(route="/", on_load=[ProjectListState.on_load])
def index():
    """Main page displaying the list of projects.

    This is the default landing page of the application.
    """
    return project_list_page()


# Declare the project detail page with URL parameter
@rx.page(route="/project/[project_id_param]")
def project_detail():
    """Project detail page displaying all information about a specific project.

    The project_id is extracted from the URL path.
    """
    return project_detail_page()


# Declare the task detail page with URL parameter
@rx.page(route="/task/[task_id_param]")
def task_detail():
    """Task detail page displaying all information about a specific task.

    The task_id is extracted from the URL path.
    """
    return task_detail_page()


# Declare the kanban board page
@rx.page(route="/kanban", on_load=[KanbanState.on_load])
def kanban():
    """Kanban board page displaying all tasks across all projects.

    This page shows a kanban view of all tasks accessible to the current user.
    """
    return kanban_page()
