import reflex as rx
from gws_reflex_main import main_component, translate

from ..common.page_layout import page_layout
from ..common.planning_grid.planning_grid import planning_grid
from . import planning_translations  # noqa: F401  (side effect: registers translations)
from .planning_state import PlanningState, PlanningWarningGroupDTO


def _week_navigation() -> rx.Component:
    """Week cursor (previous / label / next), "Today" and "Duplicate previous week",
    rendered on the header line next to the page title."""
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


def _warnings_button() -> rx.Component:
    """Opens the warnings dialog, shown only when the displayed week has warnings.

    Planning is indicative: the button counts the problems (overload, overlapping
    slots, overdue unscheduled tasks) without ever blocking an action.
    """
    # "pink" is a real Radix color name, aliased in gws_theme.css onto the
    # Constellab brand's tertiary (pink) hue - all warnings share it so they read
    # as one visual "attention" language rather than several different alerts.
    return rx.cond(
        PlanningState.warning_count > 0,
        rx.button(
            rx.icon("triangle_alert", size=16),
            # to_string(): translate() interpolates through the JS `replace`, which
            # rejects a number var as the replacement.
            translate(
                "planning.warnings.button",
                {"count": PlanningState.warning_count.to_string()},
            ),
            on_click=PlanningState.open_warnings_dialog,
            variant="soft",
            color_scheme="pink",
            size="2",
            radius="large",
        ),
    )


def _warning_group(group: PlanningWarningGroupDTO) -> rx.Component:
    """One titled category of warnings, as a bullet list of its entries."""
    return rx.vstack(
        rx.text(group.title, size="2", weight="bold"),
        rx.list.unordered(
            rx.foreach(
                group.lines,
                lambda line: rx.list.item(rx.text(line, size="2")),
            ),
            padding_left="1.25rem",
        ),
        spacing="1",
        align_items="start",
        width="100%",
    )


def _warnings_dialog() -> rx.Component:
    """Lists every warning of the displayed week, grouped by category."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(translate("planning.warnings.title")),
            rx.vstack(
                rx.foreach(PlanningState.warning_groups, _warning_group),
                spacing="4",
                align_items="start",
                width="100%",
                max_height="60vh",
                overflow_y="auto",
            ),
            rx.hstack(
                rx.button(
                    translate("planning.warnings.close"),
                    on_click=PlanningState.set_warnings_dialog_open(False),
                    variant="soft",
                    color_scheme="gray",
                ),
                justify="end",
                margin_top="16px",
                width="100%",
            ),
        ),
        open=PlanningState.warnings_dialog_open,
        on_open_change=PlanningState.set_warnings_dialog_open,
    )


def planning_page() -> rx.Component:
    """Planning page: a person x day weekly grid to schedule and confirm work."""
    return main_component(
        page_layout(
            rx.vstack(
                _duplicate_week_dialog(),
                _warnings_dialog(),
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
            header_content=rx.hstack(
                rx.heading(translate("planning.title"), size="6"),
                rx.hstack(
                    _warnings_button(),
                    _week_navigation(),
                    spacing="3",
                    align="center",
                    wrap="wrap",
                ),
                justify="between",
                align="center",
                spacing="3",
                wrap="wrap",
                width="100%",
            ),
            height="100vh",
        )
    )
