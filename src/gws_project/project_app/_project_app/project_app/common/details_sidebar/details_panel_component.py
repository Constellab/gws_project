"""The details panel: the task/project sidebar, as a right-hand panel over any screen.

Rendered by the screens that list work owned elsewhere (Kanban, Gantt, Planning, My work),
next to their dialogs. It is the same sidebar the detail pages show on their right, plus
the button that leaves for the full page.
"""

import reflex as rx
from gws_reflex_main import translate

from ..projects.project_status_chip_component import project_status_chip
from ..tasks.task_components import task_icon_component
from . import (
    details_sidebar_translations,  # noqa: F401  (side effect: registers translations)
)
from .details_panel_state import DetailsPanelState
from .details_sidebar_parts import sidebar_section_label
from .project_details_sections import project_details_sections
from .task_details_sections import task_details_sections


def _panel_title(title: rx.Var[str]) -> rx.Component:
    """Create the panel's heading.

    :param title: The name of the task or project being shown
    :type title: rx.Var[str]
    :return: The heading component
    :rtype: rx.Component
    """
    return rx.heading(title, size="4")


def _panel_header(title: rx.Var[str], open_label: rx.Var[str]) -> rx.Component:
    """Create the panel's heading row: what it shows, how to open it, how to close it.

    :param title: The section title ("Task details" / "Project details")
    :type title: rx.Var[str]
    :param open_label: The label of the button leaving for the detail page
    :type open_label: rx.Var[str]
    :return: The heading row component
    :rtype: rx.Component
    """
    return rx.hstack(
        sidebar_section_label(title),
        rx.spacer(),
        # A link, not a button firing a redirect: react-router then fetches the detail
        # page's code as soon as the panel renders ("prefetch"), so the click itself has
        # nothing left to wait for. Closing the panel is all the handler still does.
        rx.link(
            rx.button(
                rx.icon("external-link", size=14),
                open_label,
                size="1",
                variant="soft",
            ),
            href=DetailsPanelState.detail_url,
            on_click=DetailsPanelState.close,
            custom_attrs={"prefetch": "render"},
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon("x", size=16),
                variant="ghost",
                color_scheme="gray",
                on_click=DetailsPanelState.close,
            ),
            content=translate("details_sidebar.panel.close"),
        ),
        width="100%",
        align="center",
        spacing="2",
    )


def _task_panel_content() -> rx.Component:
    """Create the panel's content for a task.

    :return: The task content component
    :rtype: rx.Component
    """
    return rx.vstack(
        _panel_header(
            translate("details_sidebar.task.title"),
            translate("details_sidebar.panel.open_task"),
        ),
        # The panel is opened from screens that do not name what was clicked, so unlike
        # the detail page - which has a header and a breadcrumb - it repeats the title.
        rx.hstack(
            task_icon_component(DetailsPanelState.task, size="4"),
            _panel_title(DetailsPanelState.task.title),
            width="100%",
            align="center",
            spacing="2",
            wrap="wrap",
        ),
        task_details_sections(
            task=DetailsPanelState.task,
            created_at_text=DetailsPanelState.created_at_text,
            last_modified_at_text=DetailsPanelState.last_modified_at_text,
            parent_task=DetailsPanelState.parent_task,
            subtask_members=DetailsPanelState.subtask_members,
            project=DetailsPanelState.task_project,
            on_status_change=DetailsPanelState.update_status,
            on_priority_change=DetailsPanelState.update_priority,
        ),
        width="100%",
        spacing="5",
        align_items="start",
    )


def _project_panel_content() -> rx.Component:
    """Create the panel's content for a project.

    :return: The project content component
    :rtype: rx.Component
    """
    return rx.vstack(
        _panel_header(
            translate("details_sidebar.project.title"),
            translate("details_sidebar.panel.open_project"),
        ),
        rx.hstack(
            _panel_title(DetailsPanelState.project.title),
            project_status_chip(DetailsPanelState.project.status, size="1"),
            width="100%",
            align="center",
            spacing="2",
            wrap="wrap",
        ),
        project_details_sections(
            project=DetailsPanelState.project,
            project_users=DetailsPanelState.project_users,
            created_at_text=DetailsPanelState.created_at_text,
            last_modified_at_text=DetailsPanelState.last_modified_at_text,
        ),
        width="100%",
        spacing="5",
        align_items="start",
    )


def details_panel() -> rx.Component:
    """Create the details panel.

    Add it beside a page's dialogs, inside `main_component`, on every screen whose rows
    open it.

    A plain fixed overlay rather than `rx.drawer`: the drawer swallows the pointer events
    of anything nested in it, which left the status and priority chips unable to open
    their popover. This is the same shape gws_core's own right-sidebar overlay uses, so
    the panel behaves like the sidebar it mirrors. Closing is the backdrop or the close
    button; there is no focus trap and no Escape, exactly as in that overlay.

    :return: The details panel component
    :rtype: rx.Component
    """
    return rx.cond(
        DetailsPanelState.is_open,
        rx.fragment(
            # Backdrop
            rx.box(
                position="fixed",
                top="0",
                left="0",
                right="0",
                bottom="0",
                background="var(--color-overlay)",
                z_index="998",
                on_click=DetailsPanelState.close,
                class_name="details-panel-backdrop",
            ),
            # Panel
            rx.box(
                rx.cond(
                    DetailsPanelState.kind == "task",
                    rx.cond(DetailsPanelState.task, _task_panel_content()),
                    rx.cond(DetailsPanelState.project, _project_panel_content()),
                ),
                position="fixed",
                top="0",
                right="0",
                bottom="0",
                width="min(420px, 92vw)",
                padding="1.5rem",
                overflow_y="auto",
                background="var(--color-panel-solid)",
                border_left="1px solid var(--gray-4)",
                box_shadow="-4px 0 20px var(--gray-a5)",
                z_index="999",
                class_name="details-panel",
            ),
        ),
    )
