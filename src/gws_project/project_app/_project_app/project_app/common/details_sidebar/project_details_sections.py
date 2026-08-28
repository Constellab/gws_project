"""The body of a project details sidebar, shared by the project detail page and the panel.

Only the sections are built here: each caller renders its own heading row (the detail page
shows a close button, the panel adds an "Open this project" button), then stacks these
sections underneath, so both read exactly the same.
"""

import reflex as rx
from gws_project.project.project_dto import ProjectDTO
from gws_reflex_main import translate, user_inline_component

from ..company_app_router import CompanyAppRouter
from ..progress_ring import progress_ring
from . import (
    details_sidebar_translations,  # noqa: F401  (side effect: registers translations)
)
from .details_sidebar_parts import (
    sidebar_date_range,
    sidebar_metadata_section,
    sidebar_section_label,
)


def project_details_sections(
    project: rx.Var[ProjectDTO],
    project_users: rx.Var[list],
    created_at_text: rx.Var[str],
    last_modified_at_text: rx.Var[str],
) -> rx.Component:
    """Create the sections of a project details sidebar.

    :param project: The project to describe
    :type project: rx.Var[ProjectDTO]
    :param project_users: The project's members, as ProjectUserDTOs
    :type project_users: rx.Var[list]
    :param created_at_text: The pre-formatted creation timestamp
    :type created_at_text: rx.Var[str]
    :param last_modified_at_text: The pre-formatted last-modified timestamp
    :type last_modified_at_text: rx.Var[str]
    :return: The project details sections
    :rtype: rx.Component
    """
    return rx.vstack(
        # Centered progress ring
        rx.flex(
            progress_ring(project.progress, size="big"),
            justify="center",
            width="100%",
            margin_bottom="0.5rem",
        ),
        # Manager section
        rx.vstack(
            sidebar_section_label(translate("details_sidebar.project.manager")),
            user_inline_component(project.project_manager),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Company section (only shown when the project is linked to a company)
        rx.cond(
            project.company,
            rx.vstack(
                sidebar_section_label(translate("details_sidebar.project.company")),
                rx.link(
                    project.company.name,
                    href=CompanyAppRouter.get_company_detail_url(project.company.id),
                    size="2",
                    weight="medium",
                ),
                spacing="2",
                align_items="start",
                width="100%",
            ),
        ),
        # Dates section
        rx.vstack(
            sidebar_section_label(translate("details_sidebar.project.dates")),
            sidebar_date_range(project.start_date_text, project.due_date_text),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Members section
        rx.vstack(
            sidebar_section_label(translate("details_sidebar.project.members")),
            rx.cond(
                project_users.length() > 0,
                rx.vstack(
                    rx.foreach(
                        project_users,
                        lambda project_user: user_inline_component(project_user.user),
                    ),
                    spacing="2",
                    align_items="start",
                    width="100%",
                ),
                rx.text(
                    translate("details_sidebar.project.no_members"), size="2", color="gray"
                ),
            ),
            spacing="2",
            align_items="start",
            width="100%",
        ),
        # Divider + metadata section
        sidebar_metadata_section(
            created_by=project.created_by,
            created_at_text=created_at_text,
            last_modified_by=project.last_modified_by,
            last_modified_at_text=last_modified_at_text,
        ),
        width="100%",
        spacing="5",
        align_items="start",
    )
