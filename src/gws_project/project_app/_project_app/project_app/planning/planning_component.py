import reflex as rx
from gws_reflex_main import main_component, translate
from gws_reflex_main.components.reflex_user_components import user_select

from ..common.page_layout import page_layout
from ..common.planning_grid.planning_grid import planning_grid
from . import planning_translations  # noqa: F401  (side effect: registers translations)
from .planning_state import PlanningState


def _week_navigation() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("chevron-left", size=16),
            on_click=PlanningState.go_to_previous_week,
            variant="surface",
            color_scheme="gray",
        ),
        rx.text(PlanningState.week_label, size="3", weight="medium"),
        rx.button(
            rx.icon("chevron-right", size=16),
            on_click=PlanningState.go_to_next_week,
            variant="surface",
            color_scheme="gray",
        ),
        rx.button(
            translate("planning.week.current"),
            on_click=PlanningState.go_to_current_week,
            variant="soft",
            color_scheme="gray",
        ),
        rx.button(
            translate("planning.duplicate_previous_week"),
            on_click=PlanningState.open_duplicate_dialog,
            variant="soft",
        ),
        spacing="3",
        align="center",
        wrap="wrap",
    )


def _filter_bar() -> rx.Component:
    """Filter bar: project, company, and person selects, applied to both the grid
    and the left-hand task panel, plus a clear-filters button."""
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(
                placeholder=translate("planning.filters.all_projects"),
                width="200px",
            ),
            rx.select.content(
                rx.foreach(
                    PlanningState.project_options,
                    lambda opt: rx.select.item(opt[1], value=opt[0]),
                )
            ),
            value=PlanningState.selected_project_id,
            on_change=PlanningState.handle_project_change,
        ),
        rx.select.root(
            rx.select.trigger(
                placeholder=translate("planning.filters.all_companies"),
                width="200px",
            ),
            rx.select.content(
                rx.foreach(
                    PlanningState.company_options,
                    lambda opt: rx.select.item(opt[1], value=opt[0]),
                )
            ),
            value=PlanningState.selected_company_id,
            on_change=PlanningState.handle_company_change,
        ),
        user_select(
            users=PlanningState.available_users,
            placeholder=translate("planning.filters.all_users"),
            value=PlanningState.selected_user_id,
            on_change=PlanningState.handle_user_change,
            width="200px",
        ),
        rx.button(
            translate("planning.filters.clear"),
            on_click=PlanningState.clear_filters,
            variant="surface",
            size="2",
            color_scheme="gray",
            radius="large",
        ),
        spacing="3",
        wrap="wrap",
        align="center",
    )


def _duplicate_week_dialog() -> rx.Component:
    """Confirmation step for "duplicate previous week": lets the user pick which
    people's slots to include before anything is written."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(translate("planning.duplicate.title")),
            rx.dialog.description(
                translate("planning.duplicate.description"),
                size="2",
                margin_bottom="12px",
            ),
            rx.cond(
                PlanningState.duplicate_candidates.length() > 0,
                rx.vstack(
                    rx.foreach(
                        PlanningState.duplicate_candidates,
                        lambda person: rx.checkbox(
                            person[1],
                            checked=PlanningState.duplicate_selected_user_ids.contains(person[0]),
                            on_change=lambda checked: PlanningState.toggle_duplicate_person(
                                person[0], checked
                            ),
                        ),
                    ),
                    spacing="2",
                    align_items="start",
                    max_height="260px",
                    overflow_y="auto",
                    width="100%",
                ),
                rx.text(translate("planning.duplicate.no_slots"), color="gray", size="2"),
            ),
            rx.hstack(
                rx.button(
                    translate("planning.duplicate.cancel"),
                    on_click=PlanningState.set_duplicate_dialog_open(False),
                    variant="soft",
                    color_scheme="gray",
                ),
                rx.button(
                    translate("planning.duplicate.confirm"),
                    on_click=PlanningState.confirm_duplicate_week,
                    disabled=PlanningState.duplicate_selected_user_ids.length() == 0,
                ),
                justify="end",
                spacing="3",
                margin_top="16px",
                width="100%",
            ),
        ),
        open=PlanningState.duplicate_dialog_open,
        on_open_change=PlanningState.set_duplicate_dialog_open,
    )


def _dismissible_banner(text: rx.Var[str], color_scheme: str, banner_key: str) -> rx.Component:
    return rx.hstack(
        rx.callout(
            text,
            icon="triangle_alert",
            color_scheme=color_scheme,
            role="alert",
            width="100%",
        ),
        rx.icon_button(
            rx.icon("x", size=14),
            on_click=PlanningState.dismiss_banner(banner_key),
            variant="ghost",
            color_scheme="gray",
            size="1",
        ),
        width="100%",
        align="center",
        spacing="2",
    )


def _banners() -> rx.Component:
    # "pink" is a real Radix color name, aliased in gws_theme.css onto the
    # Constellab brand's tertiary (pink) hue - all warnings share it so they read
    # as one visual "attention" language rather than several different alerts.
    return rx.vstack(
        rx.cond(
            PlanningState.show_overload_banner,
            _dismissible_banner(PlanningState.overload_banner_text, "pink", "overload"),
        ),
        rx.cond(
            PlanningState.show_overlap_banner,
            _dismissible_banner(PlanningState.overlap_banner_text, "pink", "overlap"),
        ),
        rx.cond(
            PlanningState.show_overdue_banner,
            _dismissible_banner(PlanningState.overdue_banner_text, "pink", "overdue"),
        ),
        rx.cond(
            PlanningState.has_dismissed_banners,
            rx.button(
                translate("planning.banner.reopen"),
                on_click=PlanningState.reopen_banners,
                variant="ghost",
                size="1",
                color_scheme="gray",
            ),
        ),
        width="100%",
        spacing="2",
    )


def planning_page() -> rx.Component:
    """Planning page: a person x day weekly grid to schedule and confirm work."""
    return main_component(
        page_layout(
            rx.vstack(
                _week_navigation(),
                _duplicate_week_dialog(),
                _filter_bar(),
                _banners(),
                planning_grid(
                    grid_data=PlanningState.grid_data,
                    tasks=PlanningState.tasks,
                    on_slot_create=PlanningState.handle_slot_create,
                    on_slot_move=PlanningState.handle_slot_move,
                    on_slot_resize=PlanningState.handle_slot_resize,
                    on_slot_delete=PlanningState.handle_slot_delete,
                    width="100%",
                    flex="1",
                ),
                width="100%",
                spacing="3",
                align_items="start",
                height="100%",
            ),
            header_content=rx.heading(
                translate("planning.title"),
                size="6",
            ),
            height="100vh",
        )
    )
