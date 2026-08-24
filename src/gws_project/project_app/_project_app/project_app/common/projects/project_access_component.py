"""The screen shown instead of a project/task page the user cannot open.

A project or task id comes from the URL, so it is user input: a stale bookmark, a link
shared by a colleague, or a project the user was never added to are all normal
situations. Rather than letting the service exception surface as a broken page,
`ProjectPageState` records why the object could not be loaded and the detail pages render
this screen instead.
"""

import reflex as rx
from gws_reflex_main import translate

from ..project_app_router import ProjectAppRouter
from . import project_access_translations  # noqa: F401  (side effect: registers translations)
from .project_page_state import ProjectAccessError, ProjectPageState


def project_access_error_component() -> rx.Component:
    """Create the "not found / no access" screen, with a way back to the project list.

    :return: The access error component
    :rtype: rx.Component
    """
    return rx.center(
        rx.vstack(
            rx.icon(
                rx.cond(
                    ProjectPageState.access_error == ProjectAccessError.NO_ACCESS.value,
                    "lock",
                    "file-question",
                ),
                size=40,
                color="var(--gray-8)",
            ),
            rx.heading(
                rx.cond(
                    ProjectPageState.access_error == ProjectAccessError.NO_ACCESS.value,
                    translate("project_access.no_access.title"),
                    translate("project_access.not_found.title"),
                ),
                size="5",
                text_align="center",
            ),
            rx.text(
                rx.cond(
                    ProjectPageState.access_error == ProjectAccessError.NO_ACCESS.value,
                    translate("project_access.no_access.message"),
                    translate("project_access.not_found.message"),
                ),
                size="2",
                color="var(--gray-11)",
                text_align="center",
                max_width="420px",
            ),
            rx.link(
                rx.button(
                    rx.icon("arrow-left", size=16),
                    translate("project_access.back_to_projects"),
                    variant="soft",
                ),
                href=ProjectAppRouter.get_project_list_url(),
            ),
            spacing="4",
            align="center",
        ),
        width="100%",
        height="60vh",
        padding="2rem",
    )
