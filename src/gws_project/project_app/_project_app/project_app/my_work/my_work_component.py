"""My work page: a single column with the signed-in user's day and what waits behind it."""

import reflex as rx
from gws_reflex_main import main_component, translate

from ..common.my_day_list.my_day_list import my_day_list
from ..common.page_layout import page_layout
from ..common.project_app_router import ProjectAppRouter
from . import my_work_translations  # noqa: F401  (side effect: registers translations)
from .my_work_state import MyRestItemDTO, MyWorkState


def _empty_hint(message: rx.Component | str) -> rx.Component:
    """A quiet placeholder for a section that has nothing to show."""
    return rx.box(
        rx.text(message, size="2", color_scheme="gray"),
        width="100%",
        padding="1.25rem",
        border="1px dashed var(--gray-6)",
        border_radius="0.5rem",
    )


def _my_day_header() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(MyWorkState.day_label, size="3", weight="bold"),
            rx.spacer(),
            rx.text(MyWorkState.planned_label, size="2", color_scheme="gray"),
            width="100%",
            align="center",
        ),
        rx.cond(
            MyWorkState.over_capacity_note != "",
            # Same tertiary scheme as the Planning banners: an unusual load is signalled,
            # never enforced.
            rx.callout(
                MyWorkState.over_capacity_note,
                icon="info",
                size="1",
                color_scheme="pink",
                width="100%",
            ),
        ),
        width="100%",
        spacing="2",
        align_items="stretch",
    )


def _my_day_section() -> rx.Component:
    return rx.vstack(
        _my_day_header(),
        rx.cond(
            MyWorkState.has_day_items,
            my_day_list(
                items=MyWorkState.day_items,
                reorder_label=MyWorkState.reorder_label,
                on_reorder=MyWorkState.handle_reorder,
                on_item_click=MyWorkState.handle_open_task,
                width="100%",
            ),
            _empty_hint(translate("my_work.day.empty")),
        ),
        width="100%",
        spacing="3",
        align_items="stretch",
    )


def _rest_row(item: MyRestItemDTO) -> rx.Component:
    """One task of "The rest": schedule it, or open it."""
    return rx.hstack(
        rx.vstack(
            rx.cond(
                item.parent_task_title != "",
                rx.text(item.parent_task_title, size="1", color_scheme="gray"),
            ),
            rx.text(item.title, size="2", weight="medium"),
            rx.hstack(
                rx.text(item.project_title, size="1", style={"color": "var(--accent-11)"}),
                rx.cond(
                    item.scheduled_label != "",
                    rx.badge(item.scheduled_label, size="1", radius="full", color_scheme="gray"),
                ),
                spacing="2",
                align="center",
            ),
            spacing="1",
            align_items="start",
            flex="1",
            min_width="0",
            cursor="pointer",
            on_click=lambda: MyWorkState.handle_open_task(item.task_id),
        ),
        rx.cond(
            item.due_date_text != "",
            rx.cond(
                item.is_overdue,
                rx.text(
                    item.due_date_text,
                    size="1",
                    weight="bold",
                    style={"color": "var(--tertiary-11)"},
                    white_space="nowrap",
                ),
                rx.text(item.due_date_text, size="1", color_scheme="gray", white_space="nowrap"),
            ),
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon("calendar-plus", size=16),
                variant="ghost",
                color_scheme="gray",
                # Disabled once the working day is full: a slot appended outside the working
                # hours is bad data on the team Planning, so the day is rearranged there
                # instead. The tooltip says so rather than leaving a dead button unexplained.
                disabled=MyWorkState.add_to_day_disabled,
                on_click=lambda: MyWorkState.handle_add_to_my_day(item.task_id),
            ),
            content=MyWorkState.add_to_day_hint,
        ),
        width="100%",
        align="center",
        spacing="3",
        padding="0.625rem 0.875rem",
        background="var(--card-background)",
        border="1px solid var(--gray-6)",
        border_radius="0.5rem",
    )


def _the_rest_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                translate("my_work.rest.title"),
                size="2",
                weight="medium",
                color_scheme="gray",
            ),
            rx.badge(MyWorkState.rest_count, radius="full", color_scheme="gray"),
            width="100%",
            align="center",
            spacing="2",
        ),
        rx.cond(
            MyWorkState.has_rest_items,
            rx.vstack(
                rx.foreach(MyWorkState.rest_items, _rest_row),
                width="100%",
                spacing="2",
                align_items="stretch",
            ),
            _empty_hint(translate("my_work.rest.empty")),
        ),
        width="100%",
        spacing="3",
        align_items="stretch",
    )


def _nothing_assigned() -> rx.Component:
    """Whole-page empty state: work only ever arrives here by assignment or scheduling."""
    return rx.vstack(
        rx.icon("inbox", size=32, color="var(--gray-8)"),
        rx.heading(translate("my_work.empty.title"), size="4"),
        rx.text(
            translate("my_work.empty.description"),
            size="2",
            color_scheme="gray",
            text_align="center",
        ),
        rx.link(translate("my_work.empty.link"), href=ProjectAppRouter.get_kanban_url()),
        width="100%",
        spacing="3",
        align="center",
        padding="3rem 1rem",
    )


def my_work_page() -> rx.Component:
    """My work page: a personal, cross-project reading of today and what comes next.

    A single narrow column, two stacked sections and no filters: the value of the screen is
    its brevity, so it deliberately offers no dashboard and no person selector.
    """
    return main_component(
        page_layout(
            rx.cond(
                MyWorkState.is_empty,
                _nothing_assigned(),
                rx.vstack(
                    _my_day_section(),
                    _the_rest_section(),
                    width="100%",
                    spacing="6",
                    align_items="stretch",
                ),
            ),
            header_content=rx.heading(translate("my_work.title"), size="6"),
            max_content_width="720px",
            center_content=True,
        )
    )
