import reflex as rx
from gws_reflex_main import register_gws_reflex_app

from .admin.admin_component import admin_page
from .admin.admin_state import AdminState
from .company.company_detail_component import company_detail_page
from .company.company_list_component import company_list_page
from .company.company_list_state import CompanyListState
from .gantt.gantt_page_component import gantt_page_component
from .gantt.gantt_page_state import GanttPageState
from .kanban.kanban_component import kanban_page
from .kanban.kanban_state import KanbanState
from .note_detail.note_detail_component import note_detail_page
from .note_detail.note_detail_state import NoteDetailState
from .planning.planning_component import planning_page
from .planning.planning_state import PlanningState
from .project_detail.project_detail_component import project_detail_page
from .project_list.project_list_component import project_list_page
from .project_list.project_list_state import ProjectListState
from .task_detail.task_detail_component import task_detail_page
from .template.project_template_detail.project_template_detail_component import (
    project_template_detail_page,
)
from .template.project_template_list.project_template_list_component import (
    project_template_list_page,
)
from .template.project_template_list.project_template_list_state import ProjectTemplateListState
from .template.task_template_detail.task_template_detail_component import task_template_detail_page

app = register_gws_reflex_app()


# Declare the project list page as the index page
@rx.page(route="/", on_load=[ProjectListState.on_load])
def index():
    """Main page displaying the list of projects.

    This is the default landing page of the application.
    """
    return project_list_page()


# Declare the task detail page with URL parameter
@rx.page(route="/project/task/[task_id_param]")
def task_detail():
    """Task detail page displaying all information about a specific task.

    The task_id is extracted from the URL path.
    """
    return task_detail_page()


# Declare the note detail page with URL parameter
@rx.page(route="/project/note/[note_id_param]", on_load=[NoteDetailState.on_load])
def note_detail():
    """Note detail page displaying a single note in a full-page rich-text editor.

    The note_id is extracted from the URL path.
    """
    return note_detail_page()


# Declare the project detail page with URL parameter
@rx.page(route="/project/[project_id_param]")
def project_detail():
    """Project detail page displaying all information about a specific project.

    The project_id is extracted from the URL path.
    """
    return project_detail_page()


# Declare the company list page
@rx.page(route="/companies", on_load=[CompanyListState.on_load])
def company_list():
    """Company list page displaying all companies.

    This page shows a list of all companies, with a form to create new ones.
    """
    return company_list_page()


# Declare the company detail page with URL parameter
@rx.page(route="/company/[company_id_param]")
def company_detail():
    """Company detail page displaying all information about a specific company,
    along with the list of projects linked to it.

    The company_id is extracted from the URL path.
    """
    return company_detail_page()


# Declare the kanban board page
@rx.page(route="/kanban", on_load=[KanbanState.on_load])
def kanban():
    """Kanban board page displaying all tasks across all projects.

    This page shows a kanban view of all tasks accessible to the current user.
    """
    return kanban_page()


# Declare the gantt chart page
@rx.page(route="/gantt", on_load=[GanttPageState.on_load])
def gantt():
    """Gantt chart page displaying all projects with their root tasks.

    This page shows a timeline view of all projects and their root tasks.
    """
    return gantt_page_component()


# Declare the planning page
@rx.page(route="/planning", on_load=[PlanningState.on_load])
def planning():
    """Planning page: a person x day weekly grid to schedule and confirm work."""
    return planning_page()


# Declare the template list page
@rx.page(route="/templates", on_load=[ProjectTemplateListState.on_load])
def template_list():
    """Template list page displaying all project templates.

    This page shows a list of all available project templates.
    """
    return project_template_list_page()


# Declare the template detail page with URL parameter
@rx.page(route="/template/project/[project_template_id_param]")
def project_template_detail():
    """Template detail page displaying all information about a specific template.

    The template_id is extracted from the URL path.
    """
    return project_template_detail_page()


# Declare the template detail page with URL parameter


@rx.page(route="/template/task/[task_template_id_param]")
def task_template_detail():
    """Template detail page displaying all information about a specific template.

    The template_id is extracted from the URL path.
    """
    return task_template_detail_page()


# Declare the admin page
@rx.page(route="/admin", on_load=[AdminState.on_load])
def admin():
    """Admin page: language, roles, and (admin-only) global working hours."""
    return admin_page()
