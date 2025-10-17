import reflex as rx
from gws_reflex_main import add_unauthorized_page, get_theme

from .project_detail.project_detail_component import project_detail_page
from .project_detail.project_detail_state import ProjectDetailState
from .project_list.project_list_component import project_list_page
from .project_list.project_list_state import ProjectListState

app = rx.App(
    theme=get_theme(),
    stylesheets=["/style.css"],
)


# Declare the project list page as the index page
@rx.page(route="/", on_load=ProjectListState.on_load)
def index():
    """Main page displaying the list of projects.

    This is the default landing page of the application.
    """
    return project_list_page()


# Declare the project detail page with URL parameter
@rx.page(route="/project/[project_id_param]", on_load=ProjectDetailState.on_load)
def project_detail():
    """Project detail page displaying all information about a specific project.

    The project_id is extracted from the URL path.
    """
    return project_detail_page()


# Add the unauthorized page to the app.
# This page will be displayed if the user is not authenticated
add_unauthorized_page(app)
