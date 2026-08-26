import reflex as rx
from gws_reflex_main import register_gws_reflex_app

from .common.language_init_state import LanguageInitState
from .company.company_detail_component import company_detail_page
from .company.company_list_component import company_list_page
from .company.company_list_state import CompanyListState
from .gantt.gantt_page_component import gantt_page_component
from .gantt.gantt_page_state import GanttPageState
from .home.home_component import home_page
from .home.home_state import HomeState
from .kanban.kanban_component import kanban_page
from .kanban.kanban_state import KanbanState
from .my_work.my_work_component import my_work_page
from .my_work.my_work_state import MyWorkState
from .note_detail.note_detail_component import note_detail_page
from .note_detail.note_detail_state import NoteDetailState
from .planning.planning_component import planning_page
from .planning.planning_state import PlanningState
from .project_detail.project_detail_component import project_detail_page
from .project_list.project_list_component import project_list_page
from .project_list.project_list_state import ProjectListState
from .settings.settings_component import settings_page
from .settings.settings_state import SettingsState
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


# Every page initialises the language first. on_load runs before the layout mounts (which
# is where page_layout also triggers it), and the states resolve their texts and dates
# server-side, so without this the first render would use the shared default language
# instead of the app's.
_LANGUAGE_FIRST = LanguageInitState.ensure_default_language


# Declare the Home page as the index page: arriving on the app shows what the team is
# doing, not the raw project list (which lives at /projects).
@rx.page(route="/", on_load=[_LANGUAGE_FIRST, HomeState.on_load])
def index():
    """Home page: the ways into the app, then what the team has been doing recently.

    A derived, read-only screen: it re-reads the tasks, planning slots and activity trail
    that other pages own, and is bounded to the projects the signed-in user belongs to.
    """
    return home_page()


# Declare the project list page
@rx.page(route="/projects", on_load=[_LANGUAGE_FIRST, ProjectListState.on_load])
def project_list():
    """Page displaying the list of the projects the current user is a member of."""
    return project_list_page()


# Declare the task detail page with URL parameter
@rx.page(route="/project/task/[task_id_param]", on_load=[_LANGUAGE_FIRST])
def task_detail():
    """Task detail page displaying all information about a specific task.

    The task_id is extracted from the URL path.
    """
    return task_detail_page()


# Declare the note detail page with URL parameter
@rx.page(
    route="/project/note/[note_id_param]",
    on_load=[_LANGUAGE_FIRST, NoteDetailState.on_load],
)
def note_detail():
    """Note detail page displaying a single note in a full-page rich-text editor.

    The note_id is extracted from the URL path.
    """
    return note_detail_page()


# Declare the project detail page with URL parameter
@rx.page(route="/project/[project_id_param]", on_load=[_LANGUAGE_FIRST])
def project_detail():
    """Project detail page displaying all information about a specific project.

    The project_id is extracted from the URL path.
    """
    return project_detail_page()


# Declare the company list page
@rx.page(route="/companies", on_load=[_LANGUAGE_FIRST, CompanyListState.on_load])
def company_list():
    """Company list page displaying all companies.

    This page shows a list of all companies, with a form to create new ones.
    """
    return company_list_page()


# Declare the company detail page with URL parameter
@rx.page(route="/company/[company_id_param]", on_load=[_LANGUAGE_FIRST])
def company_detail():
    """Company detail page displaying all information about a specific company,
    along with the list of projects linked to it.

    The company_id is extracted from the URL path.
    """
    return company_detail_page()


# Declare the kanban board page
@rx.page(route="/kanban", on_load=[_LANGUAGE_FIRST, KanbanState.on_load])
def kanban():
    """Kanban board page displaying all tasks across all projects.

    This page shows a kanban view of all tasks accessible to the current user.
    """
    return kanban_page()


# Declare the gantt chart page
@rx.page(route="/gantt", on_load=[_LANGUAGE_FIRST, GanttPageState.on_load])
def gantt():
    """Gantt chart page displaying all projects with their root tasks.

    This page shows a timeline view of all projects and their root tasks.
    """
    return gantt_page_component()


# Declare the My work page
@rx.page(route="/my-work", on_load=[_LANGUAGE_FIRST, MyWorkState.on_load])
def my_work():
    """My work page: the signed-in user's day and their remaining assigned tasks.

    A derived, strictly personal view: it reads the existing tasks and planning slots,
    and never shows another member's work.
    """
    return my_work_page()


# Declare the planning page
@rx.page(route="/planning", on_load=[_LANGUAGE_FIRST, PlanningState.on_load])
def planning():
    """Planning page: a person x day weekly grid to schedule and confirm work."""
    return planning_page()


# Declare the template list page
@rx.page(route="/templates", on_load=[_LANGUAGE_FIRST, ProjectTemplateListState.on_load])
def template_list():
    """Template list page displaying all project templates.

    This page shows a list of all available project templates.
    """
    return project_template_list_page()


# Declare the template detail page with URL parameter
@rx.page(
    route="/template/project/[project_template_id_param]", on_load=[_LANGUAGE_FIRST]
)
def project_template_detail():
    """Template detail page displaying all information about a specific template.

    The template_id is extracted from the URL path.
    """
    return project_template_detail_page()


# Declare the template detail page with URL parameter


@rx.page(route="/template/task/[task_template_id_param]", on_load=[_LANGUAGE_FIRST])
def task_template_detail():
    """Template detail page displaying all information about a specific template.

    The template_id is extracted from the URL path.
    """
    return task_template_detail_page()


# Declare the settings page
@rx.page(route="/settings", on_load=[_LANGUAGE_FIRST, SettingsState.on_load])
def settings():
    """Settings page: language, roles, and (admin-only) global working hours."""
    return settings_page()
