"""Home page: where to go next, and what the team has been doing."""

import reflex as rx
from gws_reflex_main import main_component, translate, user_inline_component

from ..common.page_layout import page_layout
from ..common.project_app_router import ProjectAppRouter
from . import home_translations  # noqa: F401  (side effect: registers translations)
from .home_state import HomeActivityGroupDTO, HomeActivityRowDTO, HomeState


def _quick_access_card(
    icon: str,
    title: rx.Var | str,
    description: rx.Var | str,
    href: str,
    stat: rx.Var | None = None,
) -> rx.Component:
    """One card of the quick-access grid: a way in, plus how much waits behind it.

    :param icon: The Lucide icon shown in the card's tile
    :type icon: str
    :param title: The card's title, usually a translate() var
    :type title: rx.Var | str
    :param description: What the destination page is for
    :type description: rx.Var | str
    :param href: The route the card opens
    :type href: str
    :param stat: A live count line, e.g. "3 scheduled today". Omitted on the cards whose
        destination has no single number worth summarising.
    :type stat: rx.Var | None
    :return: The card component
    :rtype: rx.Component
    """
    body = [
        rx.hstack(
            rx.box(
                rx.icon(icon, size=22, color="var(--accent-contrast, var(--accent-1))"),
                background="var(--accent-9)",
                border_radius="10px",
                padding="0.625rem",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            rx.spacer(),
            rx.icon("arrow-right", size=18, color="var(--accent-11)"),
            width="100%",
            align="start",
        ),
        rx.heading(title, size="4"),
        rx.text(description, size="2", color_scheme="gray"),
    ]

    if stat is not None:
        body.append(rx.spacer())
        body.append(rx.text(stat, size="2", weight="medium", style={"color": "var(--accent-11)"}))

    return rx.link(
        rx.vstack(
            *body,
            height="100%",
            width="100%",
            spacing="3",
            align_items="start",
        ),
        href=href,
        width="100%",
        height="100%",
        padding="1.25rem",
        background="var(--card-background)",
        border="1px solid var(--gray-4)",
        border_radius="14px",
        text_decoration="none",
        color="inherit",
        style={":hover": {"borderColor": "var(--accent-8)"}},
    )


def _quick_access_section() -> rx.Component:
    """The four ways into the app, as in the reference Home screens of the other apps."""
    return rx.vstack(
        rx.vstack(
            # Size 5, like the activity heading below: the page header already carries the
            # "Home" title at size 6, so both sections read as its peers rather than
            # competing with it.
            rx.heading(translate("home.quick_access.title"), size="5"),
            rx.text(translate("home.quick_access.subtitle"), size="2", color_scheme="gray"),
            spacing="1",
            align_items="start",
        ),
        rx.grid(
            _quick_access_card(
                "list-checks",
                translate("home.card.my_work.title"),
                translate("home.card.my_work.description"),
                ProjectAppRouter.get_my_work_url(),
                stat=HomeState.my_work_stat,
            ),
            _quick_access_card(
                "folder",
                translate("home.card.projects.title"),
                translate("home.card.projects.description"),
                ProjectAppRouter.get_project_list_url(),
                stat=HomeState.projects_stat,
            ),
            _quick_access_card(
                "calendar-days",
                translate("home.card.planning.title"),
                translate("home.card.planning.description"),
                ProjectAppRouter.get_planning_url(),
            ),
            _quick_access_card(
                "kanban",
                translate("home.card.kanban.title"),
                translate("home.card.kanban.description"),
                ProjectAppRouter.get_kanban_url(),
            ),
            # One column on a narrow screen, two from the tablet breakpoint up: the cards
            # carry a description, so three across would squeeze it to a couple of words.
            # rx.breakpoints, not a list: Grid.columns is a typed prop and rejects a
            # sequence, unlike the plain style props that accept the list form.
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="4",
            width="100%",
            align_items="stretch",
        ),
        width="100%",
        spacing="4",
        align_items="stretch",
    )


def _activity_row(row: HomeActivityRowDTO) -> rx.Component:
    """One line of the feed: who did what, on which task, at what time.

    The task is named on its own line, which is why the message says "the task" rather than
    the task timeline's "this task" (see `TaskHistoryEvent.build_message`).
    """
    return rx.hstack(
        rx.box(
            rx.icon(row.icon, size=13),
            background="var(--accent-3)",
            color="var(--accent-9)",
            border_radius="50%",
            padding="6px",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.hstack(
                user_inline_component(row.actor, size="small"),
                rx.text(row.message, size="2", color="gray"),
                spacing="1",
                align="center",
                wrap="wrap",
            ),
            rx.hstack(
                rx.text(row.task_title, size="2", weight="medium"),
                rx.text("·", size="1", color_scheme="gray"),
                rx.text(row.project_title, size="1", style={"color": "var(--accent-11)"}),
                spacing="2",
                align="center",
                wrap="wrap",
            ),
            spacing="1",
            align_items="start",
            flex="1",
            min_width="0",
        ),
        rx.text(row.time_text, size="1", color="gray", white_space="nowrap"),
        width="100%",
        align="start",
        spacing="3",
        padding="0.625rem 0.875rem",
        background="var(--card-background)",
        border="1px solid var(--gray-4)",
        border_radius="0.5rem",
        cursor="pointer",
        on_click=lambda: HomeState.handle_open_task(row.task_id),
        key=row.id,
    )


def _activity_group(group: HomeActivityGroupDTO) -> rx.Component:
    """One day of the feed, under its "Today" / "Yesterday" / date heading."""
    return rx.vstack(
        rx.text(group.day_label, size="1", weight="bold", color_scheme="gray"),
        rx.foreach(group.rows, _activity_row),
        width="100%",
        spacing="2",
        align_items="stretch",
    )


def _activity_empty() -> rx.Component:
    """Nothing from the team in the window: says why the list is empty, not just that it is."""
    return rx.vstack(
        rx.icon("users", size=32, color="var(--gray-8)"),
        rx.heading(translate("home.activity.empty.title"), size="4"),
        rx.text(
            translate("home.activity.empty.description"),
            size="2",
            color_scheme="gray",
            text_align="center",
            max_width="420px",
        ),
        width="100%",
        spacing="3",
        align="center",
        padding="2.5rem 1rem",
    )


def _activity_section() -> rx.Component:
    """The team's recent activity: a fixed rolling window, grouped by day, newest first."""
    return rx.vstack(
        rx.vstack(
            rx.hstack(
                rx.heading(translate("home.activity.title"), size="5"),
                rx.badge(HomeState.activity_window_label, radius="full", color_scheme="gray"),
                width="100%",
                align="center",
                spacing="2",
                wrap="wrap",
            ),
            rx.cond(
                HomeState.activity_truncated_note != "",
                rx.text(HomeState.activity_truncated_note, size="1", color_scheme="gray"),
            ),
            spacing="1",
            align_items="start",
            width="100%",
        ),
        rx.cond(
            HomeState.has_activity,
            rx.vstack(
                rx.foreach(HomeState.activity_groups, _activity_group),
                width="100%",
                spacing="4",
                align_items="stretch",
            ),
            _activity_empty(),
        ),
        width="100%",
        spacing="3",
        align_items="stretch",
    )


def home_page() -> rx.Component:
    """Home page: the ways into the app, then what the team has been doing.

    Two stacked sections and no filters. The top half is fixed - the same four ways in every
    time, so the page can be used from muscle memory - and the bottom half is the only part
    that changes from one visit to the next.
    """
    return main_component(
        page_layout(
            rx.vstack(
                _quick_access_section(),
                _activity_section(),
                width="100%",
                spacing="7",
                align_items="stretch",
            ),
            max_content_width="880px",
            center_content=True,
        )
    )
