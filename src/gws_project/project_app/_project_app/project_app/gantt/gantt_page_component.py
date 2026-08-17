import reflex as rx
from gws_reflex_main import main_component, translate

from ..common.gantt.gantt_component import gantt_component
from ..common.page_layout import page_layout
from ..project_list.project_list_component import user_select
from . import gantt_translations  # noqa: F401  (side effect: registers translations)
from .gantt_page_state import GanttPageState


def _filter_bar() -> rx.Component:
    """Create the filter bar for Gantt page."""
    return rx.hstack(
        # Project title search input
        rx.input(
            placeholder=translate("gantt.filter.search_placeholder"),
            value=GanttPageState.search_title,
            on_change=GanttPageState.handle_search_title_change,
            min_width="300px",
        ),
        # Manager filter select
        user_select(
            users=GanttPageState.available_managers,
            placeholder=translate("gantt.filter.all_managers"),
            value=GanttPageState.selected_manager_id,
            on_change=GanttPageState.handle_manager_change,
            width="200px",
        ),
        # Company filter select
        rx.select.root(
            rx.select.trigger(
                placeholder=translate("gantt.filter.all_companies"),
                width="200px",
            ),
            rx.select.content(
                rx.foreach(
                    GanttPageState.company_options,
                    lambda opt: rx.select.item(
                        opt[1],
                        value=opt[0],
                    ),
                )
            ),
            value=GanttPageState.selected_company_id,
            on_change=GanttPageState.handle_company_change,
        ),
        # Clear filters button
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
        margin_top="16px",
    )


def empty_state() -> rx.Component:
    """Create an empty state component when no projects are available.

    :return: Empty state component
    :rtype: rx.Component
    """
    return rx.box(
        rx.vstack(
            rx.text("📊", font_size="48px"),
            rx.heading(translate("gantt.empty_state.title"), size="5", font_weight="600"),
            rx.text(
                translate("gantt.empty_state.description"),
                font_size="14px",
                color="gray",
            ),
            spacing="3",
            align="center",
        ),
        padding="40px",
        text_align="center",
        background_color="var(--gray-2)",
        border_radius="8px",
        margin="20px",
    )


def gantt_page_component() -> rx.Component:
    """Create the gantt page showing all projects with their root tasks.

    This page displays all projects accessible to the current user with their
    root tasks in a Gantt chart timeline view.

    :return: The gantt page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            rx.vstack(
                rx.hstack(
                    _filter_bar(),
                    rx.box(
                        rx.segmented_control.root(
                            rx.segmented_control.item(translate("gantt.view_mode.day"), value="Day"),
                            rx.segmented_control.item(translate("gantt.view_mode.week"), value="Week"),
                            rx.segmented_control.item(translate("gantt.view_mode.month"), value="Month"),
                            rx.segmented_control.item(translate("gantt.view_mode.year"), value="Year"),
                            on_change=GanttPageState.handle_view_mode_change,
                            value=GanttPageState.view_mode,
                        ),
                        margin_left="auto",
                    ),
                    width="100%",
                    align="center",
                    spacing="3",
                    margin_bottom="1rem",
                ),
                gantt_component(
                    data=GanttPageState.gantt_data,
                    view_mode=GanttPageState.view_mode,
                    on_task_click=GanttPageState.handle_task_click,
                ),
                width="100%",
                spacing="3",
                align_items="start",
                height="100%",
                class_name="gantt-container",
            ),
            header_content=rx.heading(
                translate("gantt.title"),
                size="6",
            ),
            height="100vh",
        )
    )
