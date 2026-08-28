"""The body of a task details sidebar, shared by the task detail page and the details panel.

Only the sections are built here: each caller renders its own heading row (the detail page
shows a close button, the panel adds an "Open this task" button), then stacks these
sections underneath, so both read exactly the same.
"""

from collections.abc import Callable

import reflex as rx
from gws_project.project.project_dto import ProjectDTO
from gws_project.task.task_dto import TaskDTO
from gws_reflex_main import translate, user_inline_component

from ..progress_ring import progress_ring
from ..project_app_router import ProjectAppRouter
from ..tasks.task_priority_chip_component import task_priority_chip
from ..tasks.task_status_chip_component import task_status_chip
from . import (
    details_sidebar_translations,  # noqa: F401  (side effect: registers translations)
)
from .details_sidebar_parts import (
    sidebar_date_range,
    sidebar_metadata_section,
    sidebar_section_label,
)


def task_details_sections(
    task: rx.Var[TaskDTO],
    created_at_text: rx.Var[str],
    last_modified_at_text: rx.Var[str],
    parent_task: rx.Var[TaskDTO] | None = None,
    subtask_members: rx.Var[list] | None = None,
    project: rx.Var[ProjectDTO] | None = None,
    on_status_change: Callable[[str], None] | None = None,
    on_priority_change: Callable[[str], None] | None = None,
) -> rx.Component:
    """Create the sections of a task details sidebar.

    :param task: The task to describe
    :type task: rx.Var[TaskDTO]
    :param created_at_text: The pre-formatted creation timestamp
    :type created_at_text: rx.Var[str]
    :param last_modified_at_text: The pre-formatted last-modified timestamp
    :type last_modified_at_text: rx.Var[str]
    :param parent_task: The parent task, when the task is a subtask (optional)
    :type parent_task: rx.Var[TaskDTO] | None
    :param subtask_members: The users assigned to the task's subtasks (optional)
    :type subtask_members: rx.Var[list] | None
    :param project: The project the task belongs to. Shown as a link when given; the task
        detail page omits it because its breadcrumb already names the project (optional)
    :type project: rx.Var[ProjectDTO] | None
    :param on_status_change: Handler making the status chip editable (optional)
    :type on_status_change: Callable[[str], None] | None
    :param on_priority_change: Handler making the priority chip editable (optional)
    :type on_priority_change: Callable[[str], None] | None
    :return: The task details sections
    :rtype: rx.Component
    """
    sections: list[rx.Component] = [
        # Centered progress ring (only shown once there is progress to show)
        rx.cond(
            task.progress > 0,
            rx.flex(
                progress_ring(task.progress, size="big"),
                justify="center",
                width="100%",
                margin_bottom="0.5rem",
            ),
        ),
        # Assigned to section
        rx.vstack(
            sidebar_section_label(translate("details_sidebar.task.assigned_to")),
            user_inline_component(task.assign_to),
            spacing="2",
            align_items="start",
            width="100%",
        ),
    ]

    if project is not None:
        sections.append(
            rx.cond(
                project,
                rx.vstack(
                    sidebar_section_label(translate("details_sidebar.task.project")),
                    rx.link(
                        project.title,
                        href=ProjectAppRouter.get_project_detail_url(project.id),
                        size="2",
                        weight="medium",
                    ),
                    spacing="2",
                    align_items="start",
                    width="100%",
                ),
            )
        )

    if parent_task is not None:
        sections.append(
            rx.cond(
                parent_task,
                rx.vstack(
                    sidebar_section_label(translate("details_sidebar.task.parent_task")),
                    rx.link(
                        parent_task.title,
                        href=ProjectAppRouter.get_task_detail_url(parent_task.id),
                        size="2",
                    ),
                    spacing="2",
                    align_items="start",
                    width="100%",
                ),
            )
        )

    if subtask_members is not None:
        sections.append(
            # Only a parent task has subtask members to list.
            rx.cond(
                task.allow_subtasks,
                rx.vstack(
                    sidebar_section_label(
                        translate("details_sidebar.task.subtask_members")
                    ),
                    rx.cond(
                        subtask_members.length() > 0,
                        rx.vstack(
                            rx.foreach(subtask_members, user_inline_component),
                            spacing="2",
                            align_items="start",
                            width="100%",
                        ),
                        rx.text(
                            translate("details_sidebar.task.no_members"),
                            size="2",
                            color="gray",
                            font_style="italic",
                        ),
                    ),
                    spacing="2",
                    align_items="start",
                    width="100%",
                ),
            )
        )

    sections.extend([
        # Status and Priority section (side by side)
        rx.hstack(
            rx.vstack(
                sidebar_section_label(translate("details_sidebar.task.status")),
                task_status_chip(
                    task.status,
                    on_status_change=on_status_change,
                    allow_subtask=task.allow_subtasks,
                    size="2",
                ),
                spacing="2",
                align_items="start",
            ),
            rx.spacer(),
            rx.vstack(
                sidebar_section_label(translate("details_sidebar.task.priority")),
                task_priority_chip(
                    task.priority,
                    on_priority_change=on_priority_change,
                    allow_subtask=task.allow_subtasks,
                    size="2",
                ),
                spacing="2",
                align_items="end",
            ),
            align="start",
            width="100%",
        ),
        # Dates section - hidden entirely for an undated task, so the label
        # never sits above an empty box.
        rx.cond(
            (task.start_date_text != "") | (task.due_date_text != ""),
            rx.vstack(
                sidebar_section_label(translate("details_sidebar.task.dates")),
                sidebar_date_range(task.start_date_text, task.due_date_text),
                spacing="2",
                align_items="start",
                width="100%",
            ),
        ),
        # Divider + metadata section
        sidebar_metadata_section(
            created_by=task.created_by,
            created_at_text=created_at_text,
            last_modified_by=task.last_modified_by,
            last_modified_at_text=last_modified_at_text,
        ),
    ])

    return rx.vstack(
        *sections,
        width="100%",
        spacing="5",
        align_items="start",
    )
