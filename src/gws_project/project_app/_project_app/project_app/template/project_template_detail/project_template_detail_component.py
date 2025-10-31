
import reflex as rx
from gws_reflex_main import main_component, user_inline_component
from gws_reflex_main.gws_components import rich_text_component

from ...common.detail_page_layout import detail_page_layout
from ...common.page_layout import page_layout
from ..project_template_form_dialog.project_template_form_dialog_component import \
    project_template_update_dialog
from ..project_template_form_dialog.project_template_form_dialog_state import \
    ProjectTemplateFormDialogState
from ..task_template_list.task_template_list_component import \
    task_template_list_view
from ..template_breadcrumb_state import TemplateBreadcrumbState
from .project_template_detail_state import TemplateDetailState


def template_action_menu() -> rx.Component:
    """Create the template action menu with update and delete options.

    :return: The action menu component
    :rtype: rx.Component
    """
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("ellipsis-vertical", size=18),
                variant="soft",
                color_scheme="gray"
            )
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("pencil", size=16),
                "Update Template",
                on_click=lambda: ProjectTemplateFormDialogState.open_update_dialog(TemplateDetailState.project_template)
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("trash_2", size=16),
                "Delete Template",
                color="red",
                on_click=TemplateDetailState.open_delete_template_dialog
            ),
        ),
    )


def delete_confirmation_dialog() -> rx.Component:
    """Delete confirmation dialog for templates.

    :return: The delete confirmation dialog component
    :rtype: rx.Component
    """
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Delete Template"),
            rx.alert_dialog.description(
                "Are you sure you want to delete this template? This action cannot be undone."
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Delete",
                        color_scheme="red",
                        on_click=TemplateDetailState.delete_template,
                    ),
                ),
                spacing="3",
                justify="end",
            ),
        ),
        open=TemplateDetailState.delete_dialog_opened,
        on_open_change=TemplateDetailState.set_delete_dialog_opened,
    )


def template_description_component() -> rx.Component:
    """Component for displaying and editing the template description.

    :return: The description component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Description header with edit toggle
        rx.hstack(
            rx.heading("Description", size="4", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon(
                    rx.cond(
                        TemplateDetailState.description_edit_mode,
                        "eye",
                        "pencil"
                    ),
                    size=16,
                ),
                rx.cond(
                    TemplateDetailState.description_edit_mode,
                    "View",
                    "Edit"
                ),
                variant="soft",
                size="2",
                on_click=TemplateDetailState.toggle_description_edit_mode
            ),
            width="100%",
            align="center"
        ),
        # Description content
        rx.box(
            rich_text_component(
                value=TemplateDetailState.project_template.description,
                disabled=~TemplateDetailState.description_edit_mode,
                output_event=TemplateDetailState.handle_description_change,
                custom_style=rx.cond(
                    TemplateDetailState.description_edit_mode,
                    {"minHeight": "750px", "flex": "1", "display": "block"},
                    {"padding": "0", "flex": "1", "display": "block", "minHeight": "0"}
                )
            ),
            key=TemplateDetailState.project_template.id,
            width="100%",
            flex="1",
            min_height="0",
        ),
        width="100%",
        spacing="3",
        align_items="start",
        # full height but not overflow parent
        flex="1",
        min_height="0",
    )


def info_section() -> rx.Component:
    """Create the info section (right side) with template metadata.

    :return: The info section component
    :rtype: rx.Component
    """
    return rx.vstack(
        rx.heading("Template Info", size="5", margin_bottom="1rem"),

        # Details grid - single parent grid with all fields
        rx.grid(
            # Template roles
            rx.cond(
                TemplateDetailState.template_roles.length() > 0,
                rx.fragment(
                    rx.text("Roles", size="2", color="gray", weight="medium"),
                    rx.vstack(
                        rx.foreach(
                            TemplateDetailState.template_roles,
                            lambda role: rx.badge(role, size="2", variant="soft"),
                        ),
                        spacing="2",
                        align_items="start",
                        width="100%"
                    ),
                ),
                rx.fragment()
            ),

            # Created by
            rx.text("Created by", size="2", color="gray", weight="medium"),
            user_inline_component(TemplateDetailState.project_template.created_by),

            # Created at
            rx.text("Created at", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(TemplateDetailState.project_template.created_at, format="MMM D, YYYY HH:mm"),
                size="2"
            ),

            # Last modified by
            rx.text("Last modified by", size="2", color="gray", weight="medium"),
            user_inline_component(TemplateDetailState.project_template.last_modified_by),

            # Last modified at
            rx.text("Last modified at", size="2", color="gray", weight="medium"),
            rx.text(
                rx.moment(TemplateDetailState.project_template.last_modified_at, format="MMM D, YYYY HH:mm"),
                size="2"
            ),

            columns="2",
            spacing="3",
            width="100%",
            row_gap="1rem"
        ),

        width="100%",
        spacing="3",
        align_items="start"
    )


def main_content_area() -> rx.Component:
    """Create the main content area with title, description, and task templates.

    :return: The main content area component
    :rtype: rx.Component
    """
    return rx.vstack(
        # Header with title and action menu
        rx.hstack(
            rx.heading(
                TemplateDetailState.project_template.name,
                size="8"
            ),
            template_action_menu(),
            justify="between",
            align="center",
            width="100%",
            margin_bottom="2rem"
        ),

        # Description editor
        template_description_component(),

        # Task templates section
        rx.box(height="2rem"),  # Spacer
        task_template_list_view(),

        width="100%",
        spacing="4",
    )


def project_template_detail_page() -> rx.Component:
    """Create the template detail page component.

    This page displays template details with description editor,
    info section, and action menu.

    :return: The template detail page component
    :rtype: rx.Component
    """
    return main_component(
        page_layout(
            detail_page_layout(
                main_content=main_content_area(),
                sidebar_content=info_section(),
                breadcrumbs=TemplateBreadcrumbState.breadcrumbs
            ),
            on_mount=TemplateDetailState.init,
        ),
        # Dialogs
        project_template_update_dialog(),
        delete_confirmation_dialog(),
    )
