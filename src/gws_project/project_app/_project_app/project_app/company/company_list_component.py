import reflex as rx
from gws_project.company.company_dto import CompanyDTO, CompanyStatus
from gws_reflex_main import main_component, translate

from ..common.companies.company_status_chip_component import company_status_chip
from ..common.page_layout import page_layout
from . import company_list_translations  # noqa: F401  (side effect: registers translations)
from .company_form_dialog_component import create_company_dialog
from .company_list_state import CompanyListState


def _filter_bar() -> rx.Component:
    """Create the filter bar with search and status filters.

    :return: The filter bar component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.input(
            rx.input.slot(rx.icon("search", size=16)),
            placeholder=translate("company_list.search_placeholder"),
            value=CompanyListState.search_text,
            on_change=CompanyListState.handle_search_change,
            min_width="300px",
        ),
        rx.select.root(
            rx.select.trigger(
                placeholder=translate("company_list.all_statuses"),
                width="200px",
            ),
            rx.select.content(
                *[rx.select.item(status.value, value=status.value) for status in CompanyStatus],
            ),
            value=CompanyListState.selected_status_filter,
            on_change=CompanyListState.handle_status_filter_change,
        ),
        rx.button(
            translate("company_list.clear"),
            on_click=CompanyListState.clear_filters,
            variant="surface",
            size="2",
            color_scheme="gray",
            radius="large",
        ),
        width="100%",
        spacing="3",
        wrap="wrap",
        margin_top="16px",
    )


def _row(company: CompanyDTO) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                company_status_chip(company.status),
                rx.text(company.name),
                align="center",
                spacing="3",
            ),
        ),
        rx.table.cell(rx.text(company.phone, size="2")),
        rx.table.cell(rx.text(company.address, size="2")),
        align="center",
        style={":hover": {"background_color": "var(--gray-3)"}, "cursor": "pointer"},
        on_click=lambda: CompanyListState.go_to_company(company.id),
    )


def company_list_page() -> rx.Component:
    """Create the company list page component.

    :return: The company list page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.vstack(
                _filter_bar(),
                rx.cond(
                    CompanyListState.is_loading,
                    rx.center(rx.spinner(size="3"), padding="2rem"),
                    rx.cond(
                        CompanyListState.companies.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell(translate("company_list.column_name")),
                                    rx.table.column_header_cell(translate("company_list.column_phone")),
                                    rx.table.column_header_cell(
                                        translate("company_list.column_address")
                                    ),
                                ),
                            ),
                            rx.table.body(rx.foreach(CompanyListState.companies, _row)),
                            width="100%",
                            variant="surface",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("building-2", size=48, color="gray"),
                                rx.text(
                                    translate("company_list.empty"),
                                    size="4",
                                    color="gray",
                                    margin_top="1rem",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            padding="3rem",
                            width="100%",
                        ),
                    ),
                ),
                width="100%",
                spacing="4",
            ),
            header_content=rx.hstack(
                rx.heading(translate("company_list.title"), size="6"),
                create_company_dialog(),
                justify="between",
                align="center",
                width="100%",
            ),
        )
    )
