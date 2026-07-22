import reflex as rx
from gws_project.project.project_dto import ProjectDTO
from gws_project.task.task_dto import TaskDTO
from gws_reflex_main import dialog_header, user_inline_component

from .move_task_dialog_state import MoveTaskDialogState


def _breadcrumb_separator() -> rx.Component:
    """Small chevron separator between breadcrumb segments."""
    return rx.icon("chevron-right", size=14, color="var(--gray-8)")


def _breadcrumb_segment(label: str | rx.Var[str], on_click) -> rx.Component:
    """A single clickable breadcrumb segment."""
    return rx.text(
        label,
        size="2",
        weight="medium",
        color="var(--accent-11)",
        cursor="pointer",
        white_space="nowrap",
        style={":hover": {"text_decoration": "underline"}},
        on_click=on_click,
    )


def _breadcrumb() -> rx.Component:
    """Breadcrumb trail: Projects > current project > ancestor tasks > ...

    Clicking any segment navigates back to that level.
    """
    return rx.hstack(
        _breadcrumb_segment("Projects", MoveTaskDialogState.navigate_to_projects_root),
        rx.cond(
            MoveTaskDialogState.current_project,
            rx.fragment(
                _breadcrumb_separator(),
                _breadcrumb_segment(
                    MoveTaskDialogState.current_project.title,
                    MoveTaskDialogState.navigate_to_project_root,
                ),
            ),
        ),
        rx.foreach(
            MoveTaskDialogState.breadcrumb_tasks,
            lambda task: rx.fragment(
                _breadcrumb_separator(),
                _breadcrumb_segment(
                    task.title,
                    lambda: MoveTaskDialogState.navigate_to_breadcrumb_task(task.id),
                ),
            ),
        ),
        spacing="2",
        align="center",
        wrap="wrap",
        width="100%",
    )


def _empty_state(message: str) -> rx.Component:
    """Centered empty state shown when a level has no folders."""
    return rx.center(
        rx.vstack(
            rx.icon("folder_open", size=40, color="gray"),
            rx.text(message, size="3", color="gray", margin_top="0.5rem"),
            spacing="2",
            align="center",
        ),
        padding="2.5rem",
        width="100%",
    )


def _folder_row(icon_color: str, label: rx.Var[str], secondary: rx.Component, on_click) -> rx.Component:
    """A single clickable "folder" row (a project or a task that accepts subtasks)."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.icon("folder", size=16, color=icon_color),
                rx.text(label, size="2"),
                spacing="2",
                align="center",
            )
        ),
        rx.table.cell(secondary),
        style={":hover": {"background_color": "var(--gray-3)"}, "cursor": "pointer"},
        on_click=on_click,
    )


def _project_row(project: ProjectDTO) -> rx.Component:
    return _folder_row(
        "var(--accent-9)",
        project.title,
        user_inline_component(project.project_manager, size="small"),
        lambda: MoveTaskDialogState.navigate_to_project(project),
    )


def _task_row(task: TaskDTO) -> rx.Component:
    return _folder_row(
        "var(--accent-9)",
        task.title,
        user_inline_component(task.assign_to, size="small"),
        lambda: MoveTaskDialogState.navigate_to_task(task),
    )


def _folder_table(header_label: str, rows: rx.Component) -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Name"),
                rx.table.column_header_cell(header_label),
            ),
        ),
        rx.table.body(rows),
        width="100%",
        variant="surface",
    )


def _browser_content() -> rx.Component:
    """The list of "folders" at the current level: projects at the top level, or
    tasks (root tasks / subtasks) once a project has been entered.
    """
    return rx.cond(
        MoveTaskDialogState.current_project,
        rx.cond(
            MoveTaskDialogState.tasks.length() > 0,
            _folder_table("Assignee", rx.foreach(MoveTaskDialogState.tasks, _task_row)),
            _empty_state("This folder is empty."),
        ),
        rx.cond(
            MoveTaskDialogState.projects.length() > 0,
            _folder_table("Manager", rx.foreach(MoveTaskDialogState.projects, _project_row)),
            _empty_state("No projects found."),
        ),
    )


def move_task_dialog() -> rx.Component:
    """Dialog component for moving a task to another project and/or parent task,
    using a hierarchical folder-style browser (similar to a "move to folder" picker).

    This component provides the dialog (without a trigger button). The dialog is
    controlled by the MoveTaskDialogState.dialog_opened state.

    :return: The move task dialog component
    :rtype: rx.Component
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                dialog_header(
                    "Move Task",
                    subtitle=MoveTaskDialogState.task_title,
                    close=MoveTaskDialogState.close_dialog,
                ),
                _breadcrumb(),
                rx.divider(margin_y="0.75rem"),
                rx.box(
                    _browser_content(),
                    overflow_y="auto",
                    flex="1",
                    min_height="0",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=MoveTaskDialogState.close_dialog,
                        disabled=MoveTaskDialogState.is_loading,
                    ),
                    rx.button(
                        rx.spinner(loading=MoveTaskDialogState.is_loading),
                        "Move here",
                        on_click=MoveTaskDialogState.confirm_move,
                        disabled=MoveTaskDialogState.is_loading | ~MoveTaskDialogState.can_confirm_move,
                    ),
                    margin_top="1em",
                    flex_shrink="0",
                    justify="end",
                    width="100%",
                ),
                width="100%",
                flex="1",
                min_height="0",
            ),
            max_width="600px",
            max_height="80vh",
            display="flex",
            flex_direction="column",
            on_interact_outside=MoveTaskDialogState.close_dialog,
            on_escape_key_down=MoveTaskDialogState.close_dialog,
        ),
        open=MoveTaskDialogState.dialog_opened,
    )
