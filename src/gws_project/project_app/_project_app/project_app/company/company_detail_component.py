import reflex as rx
from gws_project.project.project_dto import ProjectDTO
from gws_reflex_main import main_component, translate, user_inline_component

from ..common.companies.company_status_chip_component import company_status_chip
from ..common.company_app_router import CompanyAppRouter
from ..common.page_layout import page_layout
from ..common.progress_ring import progress_ring
from ..common.project_app_router import ProjectAppRouter
from ..common.projects.project_status_chip_component import project_status_badge
from . import company_detail_translations  # noqa: F401  (side effect: registers translations)
from .company_detail_state import CompanyDetailState
from .company_form_dialog_component import company_update_dialog
from .company_form_dialog_state import CompanyFormDialogState


def _action_menu() -> rx.Component:
    """Create the company action menu (Update only - a company can never be deleted).

    :return: The action menu component
    :rtype: rx.Component
    """
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(rx.icon("ellipsis-vertical", size=18), variant="ghost", color_scheme="gray")
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("pencil", size=16),
                translate("company_detail.update_company"),
                on_click=lambda: CompanyFormDialogState.open_update_dialog(
                    CompanyDetailState.company
                ),
            ),
        ),
    )


def _header() -> rx.Component:
    """Create the header component for the company detail page.

    :return: The header component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.heading(CompanyDetailState.company.name, size="6"),
        rx.box(
            company_status_chip(CompanyDetailState.company.status),
            margin_left="0.5rem",
        ),
        rx.spacer(),
        _action_menu(),
        width="100%",
        align="center",
        spacing="2",
    )


def _info_row(label: str, value: rx.Component) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2", color="gray", min_width="140px"),
        value,
        width="100%",
        align="center",
    )


def _info_card() -> rx.Component:
    """Create the company information card (address, SIREN, phone, logo, metadata).

    :return: The info card component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.cond(
            CompanyDetailState.logo_data_url != "",
            rx.image(
                src=CompanyDetailState.logo_data_url,
                max_height="100px",
                border_radius="0.5rem",
                margin_bottom="0.5rem",
            ),
        ),
        _info_row(
            translate("company_detail.address"), rx.text(CompanyDetailState.company.address, size="2")
        ),
        _info_row(
            translate("company_detail.siren"), rx.text(CompanyDetailState.company.siren, size="2")
        ),
        _info_row(
            translate("company_detail.phone"), rx.text(CompanyDetailState.company.phone, size="2")
        ),
        rx.divider(margin_y="0.5rem"),
        _info_row(
            translate("company_detail.created_by"),
            user_inline_component(CompanyDetailState.company.created_by, size="small"),
        ),
        _info_row(
            translate("company_detail.created_at"),
            rx.text(CompanyDetailState.created_at_text, size="1"),
        ),
        _info_row(
            translate("company_detail.last_modified_by"),
            user_inline_component(CompanyDetailState.company.last_modified_by, size="small"),
        ),
        _info_row(
            translate("company_detail.last_modified_at"),
            rx.text(CompanyDetailState.last_modified_at_text, size="1"),
        ),
        spacing="3",
        align_items="start",
        width="100%",
        max_width="500px",
        padding="1.25rem",
        border="1px solid var(--gray-5)",
        border_radius="0.75rem",
    )


def _project_row(project: ProjectDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                project_status_badge(project.status),
                rx.text(project.title),
                align="center",
                spacing="3",
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.text(project.start_date_text, size="2"),
                rx.text("→", size="2", color="var(--gray-9)"),
                rx.text(project.due_date_text, size="2", color="var(--gray-9)"),
                spacing="1",
            )
        ),
        rx.table.cell(progress_ring(project.progress)),
        rx.table.cell(user_inline_component(project.project_manager)),
        align="center",
        style={":hover": {"background_color": "var(--gray-3)"}, "cursor": "pointer"},
        on_click=lambda: rx.redirect(ProjectAppRouter.get_project_detail_url(project.id)),
    )


def _projects_section() -> rx.Component:
    """Create the section listing the projects linked to this company.

    :return: The projects section component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.heading(translate("company_detail.projects_title"), size="4"),
        rx.cond(
            CompanyDetailState.company_projects.length() > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(translate("company_detail.column_title")),
                        rx.table.column_header_cell(translate("company_detail.column_dates")),
                        rx.table.column_header_cell(translate("company_detail.column_progress")),
                        rx.table.column_header_cell(translate("company_detail.column_manager")),
                    ),
                ),
                rx.table.body(rx.foreach(CompanyDetailState.company_projects, _project_row)),
                width="100%",
                variant="surface",
            ),
            rx.text(translate("company_detail.no_projects"), size="2", color="gray"),
        ),
        width="100%",
        spacing="3",
        align_items="start",
    )


def _main_content() -> rx.Component:
    return rx.vstack(
        _info_card(),
        _projects_section(),
        width="100%",
        spacing="5",
        align_items="start",
    )


def company_detail_page() -> rx.Component:
    """Create the company detail page component.

    Displays the company's information (editable via the Update action) and the
    list of projects linked to it, each linking to its own project detail page.

    :return: The company detail page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.cond(
                CompanyDetailState.company,
                rx.vstack(
                    _header(),
                    _main_content(),
                    width="100%",
                    spacing="4",
                ),
            ),
            header_content=rx.link(
                translate("company_detail.back_to_companies"),
                href=CompanyAppRouter.get_company_list_url(),
            ),
            max_content_width="900px",
        ),
        company_update_dialog(),
    )
