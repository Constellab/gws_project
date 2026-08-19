"""Portfolio Gantt page: toolbar, legend and the timeline card."""

import reflex as rx
from gws_reflex_main import main_component, translate

from ..common.gantt.gantt_component import gantt_component
from ..common.page_layout import page_layout
from ..project_list.project_list_component import user_select
from . import gantt_translations  # noqa: F401  (side effect: registers translations)
from .gantt_page_state import GanttPageState

# Bar colours, kept in step with the chart's own palette (see PALETTE in gantt_chart.tsx).
_DONE_COLOR = "var(--accent-9)"
_REMAINING_COLOR = "var(--accent-3)"
_LATE_COLOR = "var(--tertiary-8)"

_ZOOM_LEVELS = ["day", "week", "month", "year"]


def _header_content() -> rx.Component:
    """Page header: title, live counters, subtitle and the two primary actions.

    :return: The header component
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.heading(translate("gantt.title"), size="6"),
                spacing="3",
                align="center",
            ),
            spacing="1",
            align_items="start",
        ),
        rx.spacer(),
        width="100%",
        align="center",
        spacing="3",
    )


def _toolbar() -> rx.Component:
    """Search, filters, the completed-projects toggle and the zoom selector.

    :return: The toolbar component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.hstack(
            rx.input(
                rx.input.slot(rx.icon("search", size=15)),
                placeholder=translate("gantt.filter.search_placeholder"),
                value=GanttPageState.search_title,
                on_change=GanttPageState.handle_search_title_change,
                width="230px",
                radius="small",
            ),
            user_select(
                users=GanttPageState.available_managers,
                placeholder=translate("gantt.filter.all_managers"),
                value=GanttPageState.selected_manager_id,
                on_change=GanttPageState.handle_manager_change,
                width="200px",
            ),
            rx.select.root(
                rx.select.trigger(
                    placeholder=translate("gantt.filter.all_companies"),
                    width="200px",
                    radius="small",
                ),
                rx.select.content(
                    rx.foreach(
                        GanttPageState.company_options,
                        lambda opt: rx.select.item(opt[1], value=opt[0]),
                    )
                ),
                value=GanttPageState.selected_company_id,
                on_change=GanttPageState.handle_company_change,
            ),
            rx.button(
                translate("gantt.filter.clear"),
                on_click=GanttPageState.clear_filters,
                variant="surface",
                size="2",
                color_scheme="gray",
                radius="large",
            ),
            width="100%",
            spacing="3",
            wrap="wrap",
            align="center",
        ),
        rx.hstack(
            rx.spacer(),
            rx.checkbox(
                translate("gantt.show_completed"),
                checked=GanttPageState.show_completed,
                on_change=GanttPageState.handle_show_completed_change,
                size="2",
            ),
            rx.segmented_control.root(
                *[
                    rx.segmented_control.item(
                        translate(f"gantt.view_mode.{level}"),
                        value=level.capitalize(),
                    )
                    for level in _ZOOM_LEVELS
                ],
                on_change=GanttPageState.handle_view_mode_change,
                value=GanttPageState.view_mode,
                radius="full",
                size="1",
            ),
            width="100%",
            spacing="4",
            align="center",
        ),
        width="100%",
        spacing="3",
        padding="16px 20px",
    )


def _legend_item(label, color: str) -> rx.Component:
    """One legend entry: a colour swatch followed by its label.

    :param label: The label (plain string or reactive translation var)
    :param color: CSS colour of the swatch, matching the bar it describes
    :type color: str
    :return: The legend entry
    :rtype: rx.Component
    """
    return rx.hstack(
        rx.box(
            width="18px", height="8px", border_radius="4px", background_color=color, flex_shrink="0"
        ),
        rx.text(label, size="1", color="var(--gray-11)"),
        spacing="2",
        align="center",
    )


def _legend() -> rx.Component:
    """Colour legend, plus the "today" marker on the right.

    :return: The legend band
    :rtype: rx.Component
    """
    return rx.hstack(
        _legend_item(translate("gantt.legend.done"), _DONE_COLOR),
        _legend_item(translate("gantt.legend.remaining"), _REMAINING_COLOR),
        _legend_item(translate("gantt.legend.late"), _LATE_COLOR),
        rx.spacer(),
        rx.hstack(
            rx.box(width="2px", height="12px", background_color="var(--accent-9)", opacity="0.75"),
            rx.text(translate("gantt.legend.today"), size="1", color="var(--gray-11)"),
            spacing="2",
            align="center",
        ),
        width="100%",
        spacing="4",
        align="center",
        wrap="wrap",
        padding="8px 20px",
        background_color="#fbfdfd",
        border_top="1px solid #e4ecea",
        border_bottom="1px solid #e4ecea",
    )


def gantt_page_component() -> rx.Component:
    """Create the portfolio Gantt page.

    Shows every project the user can access, grouped by status on a shared timeline, with
    its root tasks collapsible underneath.

    :return: The Gantt page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.vstack(
                # The card owns the whole chart surface, so the toolbar and legend scroll
                # with nothing and the timeline gets every remaining pixel.
                _toolbar(),
                _legend(),
                gantt_component(
                    data=GanttPageState.gantt_data,
                    view_mode=GanttPageState.view_mode,
                    show_completed=GanttPageState.show_completed,
                    recenter_token=GanttPageState.recenter_token,
                    on_task_click=GanttPageState.handle_task_click,
                ),
                width="100%",
                spacing="0",
                align_items="start",
                flex="1",
                min_height="0",
                background_color="var(--color-panel-solid, #fff)",
                border="1px solid #e4ecea",
                border_radius="20px",
                overflow="hidden",
            ),
            header_content=_header_content(),
            height="100vh",
        )
    )
